"""Local paths and settings for the backend service."""
from __future__ import annotations

from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
BACKEND_DIR = APP_DIR.parent
DATA_DIR = BACKEND_DIR / "data"
PROJECTS_DIR = DATA_DIR / "projects"

CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

DEFAULT_WHISPER_MODEL = "small"
