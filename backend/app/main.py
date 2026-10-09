"""
Milo — FastAPI application.
Serves the chat API, dataset metadata, health checks, and built React frontend.
"""

import json
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse, FileResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import CSV_PATH, GEMINI_API_KEY, APP_ENV
from .data_loader import load_orders, get_orders, get_dataset_metadata, DatasetError
from .schemas import ChatRequest, ChatResponse, HealthResponse, DatasetInfo
from .agent import (
    chat as agent_chat,
    MiloAgentError,
    MiloClientError,
    MiloSafetyError,
    MiloProviderError,
    MiloIterationLimitError,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("milo.server")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load and validate dataset once at startup; store status in app state."""
    logger.info("Initializing dataset at startup...")
    app.state.dataset_loaded = False
    app.state.dataset_metadata = None

    try:
        load_orders(CSV_PATH)
        app.state.dataset_loaded = True
        app.state.dataset_metadata = get_dataset_metadata()
        logger.info("Dataset loaded and validated successfully.")
    except DatasetError as e:
        logger.error(f"Dataset integrity validation failed at startup: {e}")
    except Exception as e:
        logger.error(f"Unexpected startup error loading dataset: {e}")

    yield


app = FastAPI(
    title="Milo",
    description="Your orders, answered.",
    version="1.0.0",
    lifespan=lifespan,
)

# ──────────────────────────── CORS ────────────────────────────
# Only enabled for local Vite development server when APP_ENV is development
if APP_ENV == "development":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# ──────────────────────────── Exception Handlers ────────────────────────────


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Return structured 422 error response in {reply: null, error: ...} shape."""
    logger.warning(f"Validation error on {request.url.path}: {exc.errors()}")
    if request.url.path.startswith("/api/chat"):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"reply": None, "error": "Invalid request: message must be a non-empty string up to 2000 characters."},
        )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
    )


@app.exception_handler(json.JSONDecodeError)
async def json_decode_exception_handler(request: Request, exc: json.JSONDecodeError):
    """Handle malformed JSON payloads."""
    logger.warning(f"Malformed JSON on {request.url.path}")
    if request.url.path.startswith("/api/chat"):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"reply": None, "error": "Malformed JSON payload."},
        )
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": "Malformed JSON payload."},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global catch-all exception handler that hides internal stack traces."""
    logger.error(f"Unhandled exception on {request.url.path}: {exc}", exc_info=True)
    if request.url.path.startswith("/api/chat"):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"reply": None, "error": "An internal error occurred. Please try again."},
        )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error."},
    )


# ──────────────────────────── API Routes ────────────────────────────


@app.get("/api/health", response_model=HealthResponse)
async def health():
    """Health check endpoint. Reports status, data readiness, and whether AI key is configured."""
    data_loaded = getattr(app.state, "dataset_loaded", False)
    ai_configured = bool(GEMINI_API_KEY and GEMINI_API_KEY.strip())

    return HealthResponse(
        status="ok" if data_loaded else "data-not-ready",
        data_loaded=data_loaded,
        ai_configured=ai_configured,
    )


@app.get("/api/dataset", response_model=DatasetInfo)
async def dataset():
    """Expose dataset metadata (record count, start date, end date) for the frontend sidebar."""
    if not getattr(app.state, "dataset_loaded", False):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Dataset is not loaded or not ready.",
        )

    metadata = getattr(app.state, "dataset_metadata", None)
    if not metadata:
        metadata = get_dataset_metadata()

    return DatasetInfo(
        record_count=metadata["record_count"],
        start_date=metadata["min_order_date"],
        end_date=metadata["max_order_date"],
    )


@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Process user message through Milo agent. Returns {reply, error}."""
    if not getattr(app.state, "dataset_loaded", False):
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"reply": None, "error": "Order dataset is not ready. Please check server logs."},
        )

    try:
        result = await agent_chat(request.message)
        return ChatResponse(
            reply=result["reply"],
            error=None,
        )
    except MiloClientError as exc:
        logger.warning(f"Milo client error: {exc}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"reply": None, "error": str(exc)},
        )
    except MiloSafetyError as exc:
        logger.warning(f"Milo safety error: {exc}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"reply": None, "error": "The request could not be processed due to safety policies."},
        )
    except MiloProviderError as exc:
        logger.error(f"Milo provider error: {exc}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"reply": None, "error": "AI service is temporarily unavailable. Please try again later."},
        )
    except MiloIterationLimitError as exc:
        logger.error(f"Milo iteration limit error: {exc}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"reply": None, "error": "Unable to complete request within allowed processing steps."},
        )
    except Exception as exc:
        logger.error(f"Unexpected chat endpoint error: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"reply": None, "error": "An unexpected error occurred processing your request."},
        )


# ──────────────────────────── Static Files & SPA Fallback ────────────

_frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"

if _frontend_dist.is_dir():
    # Mount assets directory
    assets_dir = _frontend_dist / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    # SPA catch-all fallback and root static file serving
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith("api/") or full_path == "api":
            raise HTTPException(status_code=404, detail="Not Found")
        target_file = _frontend_dist / full_path
        if full_path and target_file.is_file():
            return FileResponse(target_file)
        index_file = _frontend_dist / "index.html"
        if index_file.is_file():
            return FileResponse(index_file)
        raise HTTPException(status_code=404, detail="Frontend build index not found")
