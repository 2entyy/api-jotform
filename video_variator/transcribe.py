"""Local, offline speech-to-text via openai-whisper (no API key, no network calls once the model is cached)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass
class Transcript:
    text: str
    language: str


_MODEL_CACHE: Dict[str, object] = {}


def _get_model(model_size: str):
    if model_size not in _MODEL_CACHE:
        import whisper  # imported lazily: heavy (torch) and only needed for real transcription

        _MODEL_CACHE[model_size] = whisper.load_model(model_size)
    return _MODEL_CACHE[model_size]


def transcribe(video_path: str, model_size: str = "small") -> Transcript:
    model = _get_model(model_size)
    result = model.transcribe(video_path)
    return Transcript(
        text=str(result.get("text", "")).strip(),
        language=str(result.get("language", "pt")),
    )
