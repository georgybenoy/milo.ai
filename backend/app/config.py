"""
Milo configuration — all settings from environment variables.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root (one level up from backend/)
_project_root = Path(__file__).resolve().parent.parent.parent
load_dotenv(_project_root / ".env")

GEMINI_API_KEY: str = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL: str = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")

CSV_PATH: Path = _project_root / "orders.csv"

# Safety: never expose these to the client
MAX_TOOL_ITERATIONS: int = 5
