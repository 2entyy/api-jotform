"""Pydantic models describing a project's full editable state."""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class WordTiming(BaseModel):
    word: str
    start: float
    end: float


class Segment(BaseModel):
    id: int
    start: float
    end: float
    text: str
    words: List[WordTiming] = Field(default_factory=list)


class Trim(BaseModel):
    start: float = 0.0
    end: Optional[float] = None


class HookState(BaseModel):
    text: str = ""
    start: float = 0.0
    end: float = 4.0


class MusicState(BaseModel):
    filename: Optional[str] = None
    volume: float = 0.5
    duck_level: float = 0.15


class CriticResult(BaseModel):
    score: int
    summary: str
    suggestions: List[str] = Field(default_factory=list)


class ChatMessage(BaseModel):
    role: str
    text: str


class StylePreview(BaseModel):
    style: str
    label: str
    url: str


class Project(BaseModel):
    id: str
    created_at: str
    source_video: str
    duration: Optional[float] = None
    language: str = "pt"
    transcript: str = ""
    segments: List[Segment] = Field(default_factory=list)
    hook_options: List[str] = Field(default_factory=list)
    hook: HookState = Field(default_factory=HookState)
    caption_style: str = "impacto"
    trim: Trim = Field(default_factory=Trim)
    speed: float = 1.0
    music: MusicState = Field(default_factory=MusicState)
    critic: Optional[CriticResult] = None
    chat: List[ChatMessage] = Field(default_factory=list)
    style_previews: List[StylePreview] = Field(default_factory=list)
    status: str = "draft"
    render_url: Optional[str] = None
    variation_urls: List[str] = Field(default_factory=list)
