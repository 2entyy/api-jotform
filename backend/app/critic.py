"""Scores the video's opening the way a short-form editor would: does it hook fast?

Purely heuristic by default (keyword/pattern matching over the first few
seconds of transcript); if a local Ollama server is running, its output is
folded in as an extra, richer suggestion line — never as the score itself,
so results stay deterministic and don't require any local model to be
installed.
"""
from __future__ import annotations

import re
from typing import List

from backend.app import llm
from backend.app.schemas import CriticResult, Segment

_CURIOSITY_STARTERS = [
    "vocês pensavam", "voces pensavam", "ninguém", "ninguem", "não sabias",
    "nao sabias", "isto vai", "sabias que", "a verdade", "o segredo", "nunca",
]
_CONTRAST_WORDS = ["mas ", "não é", "nao e", "afinal", "na verdade", "só que", "so que", "porém", "porem"]


def _opening_text(segments: List[Segment], window: float = 5.0) -> str:
    parts = [s.text for s in segments if s.start < window]
    return " ".join(parts).strip()


def score_hook(segments: List[Segment]) -> CriticResult:
    opening = _opening_text(segments)
    lower = opening.lower()
    score = 4
    hits: List[str] = []
    suggestions: List[str] = []

    if any(starter in lower for starter in _CURIOSITY_STARTERS):
        score += 2
        hits.append("gancho de curiosidade claro")
    else:
        suggestions.append(
            "Começa com uma frase de curiosidade (\"vocês pensavam que...\", \"ninguém te disse que...\")"
        )

    if any(w in lower for w in _CONTRAST_WORDS):
        score += 2
        hits.append("contraste/reviravolta na abertura")
    else:
        suggestions.append("Introduz um contraste ou reviravolta logo nos primeiros segundos")

    if "?" in opening:
        score += 1
        hits.append("pergunta direta ao espectador")

    if re.search(r"\d", opening):
        score += 1
        hits.append("número concreto que ancora a atenção")

    word_count = len(opening.split())
    if word_count == 0:
        score = 1
        suggestions.append(
            "Sem fala percetível nos primeiros segundos — considera um gancho falado ou em texto"
        )
    elif word_count > 40:
        score -= 1
        suggestions.append("Abertura longa — encurta para prender a atenção mais depressa")

    score = max(1, min(10, score))

    summary = (
        "Abertura com " + ", ".join(hits) + "." if hits else "Abertura ainda genérica, sem gancho claro."
    )
    if not suggestions:
        suggestions.append("Considera reforçar a expectativa com uma imagem ou corte antes do twist")

    if llm.is_available() and opening:
        prompt = (
            "Em português europeu, numa frase curta, dá uma sugestão concreta para tornar mais "
            f"cativante esta abertura de um vídeo de Reels: {opening!r}"
        )
        extra = llm.generate(prompt)
        if extra:
            suggestions.append(extra.strip())

    return CriticResult(score=score, summary=summary, suggestions=suggestions)
