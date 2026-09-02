"""JSON-file project persistence — no database needed for a single-user local app."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from backend.app.config import PROJECTS_DIR
from backend.app.schemas import Project

MEDIA_SUBDIRS = ("uploads", "previews", "renders", "variations")


def new_project_id() -> str:
    return uuid.uuid4().hex[:12]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def project_dir(project_id: str) -> Path:
    d = PROJECTS_DIR / project_id
    for sub in MEDIA_SUBDIRS:
        (d / sub).mkdir(parents=True, exist_ok=True)
    return d


def save(project: Project) -> None:
    path = project_dir(project.id) / "project.json"
    path.write_text(project.model_dump_json(indent=2), encoding="utf-8")


def load(project_id: str) -> Optional[Project]:
    path = project_dir(project_id) / "project.json"
    if not path.exists():
        return None
    return Project.model_validate_json(path.read_text(encoding="utf-8"))


def list_projects() -> List[Project]:
    projects: List[Project] = []
    if not PROJECTS_DIR.exists():
        return projects
    for d in sorted(PROJECTS_DIR.iterdir(), reverse=True):
        if not d.is_dir():
            continue
        project = load(d.name)
        if project:
            projects.append(project)
    return projects
