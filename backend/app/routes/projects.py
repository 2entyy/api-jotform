"""REST API for the project editing workflow: upload, transcribe, style, render, variate."""
from __future__ import annotations

import random
import shutil
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from backend.app import store
from backend.app.assistant import parse_command
from backend.app.captions import STYLE_ORDER, STYLES
from backend.app.critic import score_hook
from backend.app.hooks import suggest_hooks
from backend.app.render import (
    find_default_font,
    render_micro_variation,
    render_project,
    render_style_preview,
)
from backend.app.schemas import ChatMessage, HookState, MusicState, Project, StylePreview, Trim
from backend.app.transcription import transcribe_with_words
from video_variator.effects import random_variation_params

router = APIRouter()


def _media_url(project_id: str, subdir: str, filename: str) -> str:
    return f"/media/projects/{project_id}/{subdir}/{filename}"


def _get_or_404(project_id: str) -> Project:
    project = store.load(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    return project


def _source_path(project: Project) -> Path:
    return store.project_dir(project.id) / "uploads" / project.source_video


def _save_upload(dest: Path, upload: UploadFile) -> None:
    with dest.open("wb") as f:
        shutil.copyfileobj(upload.file, f)


@router.get("", response_model=List[Project])
def list_projects() -> List[Project]:
    return store.list_projects()


@router.post("", response_model=Project)
def create_project(file: UploadFile = File(...), model: str = Form("small")) -> Project:
    project_id = store.new_project_id()
    pdir = store.project_dir(project_id)

    suffix = Path(file.filename or "video.mp4").suffix or ".mp4"
    source_name = f"source{suffix}"
    _save_upload(pdir / "uploads" / source_name, file)

    project = Project(id=project_id, created_at=store.now_iso(), source_video=source_name)

    transcript, language, segments = transcribe_with_words(str(pdir / "uploads" / source_name), model)
    project.transcript = transcript
    project.language = language
    project.segments = segments
    project.hook_options = suggest_hooks(transcript, language, count=4, seed=hash(project_id) % (2**31))
    project.hook = HookState(text=project.hook_options[0] if project.hook_options else "")
    project.critic = score_hook(segments)

    store.save(project)
    return project


@router.get("/{project_id}", response_model=Project)
def get_project(project_id: str) -> Project:
    return _get_or_404(project_id)


class ProjectUpdate(BaseModel):
    caption_style: Optional[str] = None
    hook: Optional[HookState] = None
    trim: Optional[Trim] = None
    music: Optional[MusicState] = None


@router.patch("/{project_id}", response_model=Project)
def update_project(project_id: str, update: ProjectUpdate) -> Project:
    project = _get_or_404(project_id)
    if update.caption_style is not None:
        if update.caption_style not in STYLES:
            raise HTTPException(status_code=400, detail="Estilo de legenda desconhecido")
        project.caption_style = update.caption_style
    if update.hook is not None:
        project.hook = update.hook
    if update.trim is not None:
        project.trim = update.trim
    if update.music is not None:
        project.music = update.music
    store.save(project)
    return project


@router.post("/{project_id}/music", response_model=Project)
def upload_music(project_id: str, file: UploadFile = File(...)) -> Project:
    project = _get_or_404(project_id)
    pdir = store.project_dir(project_id)
    suffix = Path(file.filename or "music.mp3").suffix or ".mp3"
    music_name = f"music{suffix}"
    _save_upload(pdir / "uploads" / music_name, file)
    project.music.filename = music_name
    store.save(project)
    return project


@router.post("/{project_id}/style-previews", response_model=List[StylePreview])
def generate_style_previews(project_id: str) -> List[StylePreview]:
    project = _get_or_404(project_id)
    source = _source_path(project)
    pdir = store.project_dir(project_id)

    previews: List[StylePreview] = []
    for style_key in STYLE_ORDER:
        out_name = f"{style_key}.mp4"
        out_path = pdir / "previews" / out_name
        render_style_preview(str(source), str(out_path), project.segments, style_key)
        previews.append(
            StylePreview(
                style=style_key,
                label=STYLES[style_key].label,
                url=_media_url(project_id, "previews", out_name),
            )
        )

    project.style_previews = previews
    store.save(project)
    return previews


@router.post("/{project_id}/critic", response_model=Project)
def recompute_critic(project_id: str) -> Project:
    project = _get_or_404(project_id)
    project.critic = score_hook(project.segments)
    store.save(project)
    return project


class CommandRequest(BaseModel):
    text: str


@router.post("/{project_id}/command", response_model=Project)
def run_command(project_id: str, body: CommandRequest) -> Project:
    project = _get_or_404(project_id)
    action = parse_command(body.text)

    project.chat.append(ChatMessage(role="user", text=body.text))

    if action.action == "remove_music":
        project.music.filename = None
    elif action.action == "strengthen_hook":
        candidates = [h for h in project.hook_options if h != project.hook.text]
        if candidates:
            project.hook.text = candidates[0]
        else:
            new_options = suggest_hooks(
                project.transcript, project.language, count=1, seed=random.randint(0, 2**31 - 1)
            )
            if new_options:
                project.hook_options.append(new_options[0])
                project.hook.text = new_options[0]
    elif action.action == "speed_up":
        project.speed = round(min(1.5, project.speed * 1.05), 3)
    elif action.action == "slow_down":
        project.speed = round(max(0.7, project.speed * 0.95), 3)
    elif action.action == "set_caption_style":
        style = action.params.get("style")
        if style in STYLES:
            project.caption_style = style

    project.chat.append(ChatMessage(role="assistant", text=action.message))
    store.save(project)
    return project


@router.post("/{project_id}/render", response_model=Project)
def render(project_id: str) -> Project:
    project = _get_or_404(project_id)
    font = find_default_font()
    if not font:
        raise HTTPException(status_code=500, detail="Nenhuma fonte .ttf encontrada no sistema")

    pdir = store.project_dir(project_id)
    source = _source_path(project)
    music_path = str(pdir / "uploads" / project.music.filename) if project.music.filename else None

    out_name = "final.mp4"
    out_path = pdir / "renders" / out_name
    render_project(project, str(source), str(out_path), font_path=font, music_path=music_path)

    project.render_url = _media_url(project_id, "renders", out_name)
    project.status = "ready"
    store.save(project)
    return project


class VariationsRequest(BaseModel):
    count: int = 5
    seed: Optional[int] = None


@router.post("/{project_id}/variations", response_model=Project)
def generate_variations(project_id: str, body: VariationsRequest) -> Project:
    project = _get_or_404(project_id)
    if not project.render_url:
        raise HTTPException(status_code=400, detail="Aprova e renderiza o vídeo primeiro")

    pdir = store.project_dir(project_id)
    source = pdir / "renders" / "final.mp4"
    rng = random.Random(body.seed)

    urls: List[str] = []
    for i in range(1, body.count + 1):
        params = random_variation_params(rng, title="")
        out_name = f"var{i}.mp4"
        out_path = pdir / "variations" / out_name
        render_micro_variation(str(source), str(out_path), params)
        urls.append(_media_url(project_id, "variations", out_name))

    project.variation_urls = urls
    store.save(project)
    return project
