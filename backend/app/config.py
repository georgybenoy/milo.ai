"""
Milo configuration — loads environment variables and exposes settings.
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger("milo.config")

# Resolve repository root relative to this file: backend/app -> backend -> repo root
REPO_ROOT: Path = Path(__file__).resolve().parent.parent.parent

# Load .env from project root
dotenv_path = REPO_ROOT / ".env"
if dotenv_path.exists():
    load_dotenv(dotenv_path)
else:
    load_dotenv()

# Settings
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
APP_ENV: str = os.getenv("APP_ENV", "development")

# CSV Path resolved relative to repo root
CSV_PATH: Path = Path(os.getenv("CSV_PATH", str(REPO_ROOT / "orders.csv"))).resolve()

MAX_TOOL_ITERATIONS: int = 5

# Check API key with a clear server-side log message (no crash at import time)
if not GEMINI_API_KEY:
    logger.warning("GEMINI_API_KEY is not set. Natural language queries requiring Gemini will fail until key is provided.")
