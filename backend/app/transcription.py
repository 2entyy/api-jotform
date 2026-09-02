"""Local, offline speech-to-text with per-word timestamps (needed for karaoke/one-word captions)."""
from __future__ import annotations

from typing import Dict, List, Tuple

from backend.app.config import DEFAULT_WHISPER_MODEL
from backend.app.schemas import Segment, WordTiming

_MODEL_CACHE: Dict[str, object] = {}


def _get_model(model_size: str):
    if model_size not in _MODEL_CACHE:
        import whisper  # heavy (torch) import, deferred until actually needed

        _MODEL_CACHE[model_size] = whisper.load_model(model_size)
    return _MODEL_CACHE[model_size]


def transcribe_with_words(
    video_path: str, model_size: str = DEFAULT_WHISPER_MODEL
) -> Tuple[str, str, List[Segment]]:
    model = _get_model(model_size)
    result = model.transcribe(video_path, word_timestamps=True)
    language = str(result.get("language", "pt"))

    segments: List[Segment] = []
    for i, seg in enumerate(result.get("segments", [])):
        words = [
            WordTiming(word=str(w["word"]).strip(), start=float(w["start"]), end=float(w["end"]))
            for w in seg.get("words", [])
            if str(w.get("word", "")).strip()
        ]
        segments.append(
            Segment(
                id=i,
                start=float(seg["start"]),
                end=float(seg["end"]),
                text=str(seg["text"]).strip(),
                words=words,
            )
        )

    full_text = " ".join(s.text for s in segments).strip()
    return full_text, language, segments
