"""
Milo — FastAPI application.
Serves the API and the built React frontend.
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .config import CSV_PATH, GEMINI_MODEL
from .data_loader import load_orders, get_orders, DatasetError
from .schemas import ChatRequest, ChatResponse, HealthResponse
from .agent import (
    chat as agent_chat,
    MiloAgentError,
    MiloClientError,
    MiloSafetyError,
    MiloProviderError,
    MiloIterationLimitError,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load CSV at startup — once, kept in memory."""
    logger.info(f"Loading orders from {CSV_PATH}")
    try:
        df = load_orders(CSV_PATH)
        logger.info(f"Loaded {len(df)} orders successfully")
    except DatasetError as e:
        logger.error(f"Dataset integrity validation failed: {e}")
    except Exception as e:
        logger.error(f"Unexpected error loading orders: {e}")
    yield


app = FastAPI(
    title="Milo",
    description="Your orders, answered.",
    version="1.0.0",
    lifespan=lifespan,
)


# ──────────────────────────── API Routes ────────────────────────────


@app.get("/api/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    try:
        df = get_orders()
        return HealthResponse(
            status="healthy",
            orders_loaded=len(df),
            model=GEMINI_MODEL,
        )
    except DatasetError as e:
        logger.warning(f"Health check reporting data-not-ready: {e}")
        return HealthResponse(
            status="data-not-ready",
            orders_loaded=0,
            model=GEMINI_MODEL,
        )
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return HealthResponse(
            status="data-not-ready",
            orders_loaded=0,
            model=GEMINI_MODEL,
        )


@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Process a chat message through the Milo agent."""
    try:
        result = await agent_chat(request.message)
        return ChatResponse(
            reply=result["reply"],
            tool_used=result.get("tool_used"),
        )
    except MiloClientError as e:
        logger.warning(f"Client error in chat: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except MiloSafetyError as e:
        logger.warning(f"Safety policy block: {e}")
        raise HTTPException(
            status_code=400,
            detail="The request could not be processed due to safety policies.",
        )
    except MiloProviderError as e:
        logger.error(f"Provider error in chat: {e}")
        raise HTTPException(
            status_code=503,
            detail="AI service is temporarily unavailable. Please try again later.",
        )
    except MiloIterationLimitError as e:
        logger.error(f"Iteration limit error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Unable to complete the query within the allowed number of steps.",
        )
    except Exception as e:
        logger.error(f"Unexpected chat error: {e}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while processing your request.",
        )


# ──────────────────────────── Static Files (React build) ────────────


# Serve the React build if it exists
_frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"

if _frontend_dist.exists():
    # Serve static assets (JS, CSS, images)
    app.mount(
        "/assets",
        StaticFiles(directory=_frontend_dist / "assets"),
        name="static-assets",
    )

    # Serve other static files in dist root (favicon, etc.)
    @app.get("/favicon.ico")
    async def favicon():
        favicon_path = _frontend_dist / "favicon.ico"
        if favicon_path.exists():
            return FileResponse(favicon_path)
        raise HTTPException(status_code=404)

    @app.get("/milo-logo.png")
    async def logo():
        logo_path = _frontend_dist / "milo-logo.png"
        if logo_path.exists():
            return FileResponse(logo_path)
        raise HTTPException(status_code=404)

    # SPA fallback — serve index.html for all unmatched routes
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Don't catch API routes
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404)
        return FileResponse(_frontend_dist / "index.html")
