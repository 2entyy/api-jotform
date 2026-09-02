"""FastAPI app entry point. Run with:

    python -m uvicorn backend.app.main:app --reload --port 8000

from the repository root (so both the `backend` and `video_variator` top-level
packages are importable).
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.app.config import CORS_ORIGINS, DATA_DIR
from backend.app.routes.projects import router as projects_router

DATA_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Video Variator", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/media", StaticFiles(directory=str(DATA_DIR)), name="media")
app.include_router(projects_router, prefix="/api/projects", tags=["projects"])


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}
