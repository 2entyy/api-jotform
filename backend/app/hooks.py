"""Suggests hook/title options for the top text-box track, from the transcript."""
from __future__ import annotations

from typing import List, Optional

from video_variator.titles import generate_titles


def suggest_hooks(transcript: str, language: str, count: int = 4, seed: Optional[int] = None) -> List[str]:
    return generate_titles(transcript, language, count, seed=seed)
