"""Heuristic, offline generation of catchy title-box captions from a transcript.

No LLM call: keywords are ranked by frequency in the transcript and dropped into
template phrases, so every variation gets a distinct, topic-relevant caption.
"""
from __future__ import annotations

import random
import re
from typing import List, Optional

WORD_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ]{3,}")

_STOPWORDS = {
    "pt": {
        "que", "para", "com", "uma", "por", "isso", "esse", "essa", "este", "esta",
        "mas", "mais", "muito", "muita", "muitos", "muitas", "como", "quando",
        "onde", "porque", "porquê", "sobre", "entre", "sem", "das", "dos", "nas",
        "nos", "num", "numa", "pelo", "pela", "isto", "aqui", "ali", "assim",
        "então", "vai", "vou", "estou", "está", "são", "foi", "ser", "ter", "tem",
        "tinha", "hoje", "agora", "depois", "antes", "não", "sim", "também",
        "ainda", "já", "todo", "toda", "todos", "todas", "algo", "alguém",
        "cada", "outro", "outra", "outros", "outras", "the", "and",
    },
    "en": {
        "that", "with", "this", "these", "those", "have", "has", "had", "just",
        "about", "into", "your", "you", "for", "are", "was", "were", "will",
        "would", "could", "should", "there", "here", "then", "than", "what",
        "when", "where", "which", "who", "why", "how", "not", "yes", "also",
        "still", "already", "every", "each", "other", "another", "from",
    },
}

_TEMPLATES = {
    "pt": [
        "O SEGREDO SOBRE {TOPIC}",
        "NINGUÉM TE CONTA ISTO SOBRE {TOPIC}",
        "{TOPIC}: A VERDADE QUE NINGUÉM DIZ",
        "ISTO MUDOU TUDO SOBRE {TOPIC}",
        "PRECISAS DE SABER ISTO SOBRE {TOPIC}",
        "A VERDADE SOBRE {TOPIC}",
        "NÃO ACREDITEI QUANDO VI ISTO",
        "{TOPIC}: O QUE NINGUÉM EXPLICA",
    ],
    "en": [
        "THE TRUTH ABOUT {TOPIC}",
        "NOBODY TELLS YOU THIS ABOUT {TOPIC}",
        "{TOPIC}: WHAT NO ONE SAYS",
        "THIS CHANGED EVERYTHING ABOUT {TOPIC}",
        "YOU NEED TO KNOW THIS ABOUT {TOPIC}",
        "THE REAL STORY BEHIND {TOPIC}",
        "I DIDN'T BELIEVE THIS AT FIRST",
        "{TOPIC}: WHAT THEY DON'T EXPLAIN",
    ],
}

_DEFAULT_TOPIC = {"pt": "ISTO", "en": "THIS"}


def extract_keywords(text: str, language: str, top_n: int = 5) -> List[str]:
    stopwords = _STOPWORDS.get(language, _STOPWORDS["pt"])
    counts: dict[str, int] = {}
    for match in WORD_RE.finditer(text.lower()):
        word = match.group()
        if word in stopwords:
            continue
        counts[word] = counts.get(word, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return [word for word, _ in ranked[:top_n]]


def generate_titles(
    text: str, language: str, count: int, seed: Optional[int] = None
) -> List[str]:
    rng = random.Random(seed)
    lang = language if language in _TEMPLATES else "pt"
    templates = list(_TEMPLATES[lang])
    rng.shuffle(templates)

    keywords = extract_keywords(text, lang) or [_DEFAULT_TOPIC[lang]]

    titles = []
    for i in range(count):
        template = templates[i % len(templates)]
        topic = keywords[i % len(keywords)].upper()
        titles.append(template.format(TOPIC=topic) if "{TOPIC}" in template else template)
    return titles


def wrap_text(text: str, max_chars: int = 22) -> str:
    words = text.split()
    lines: List[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) > max_chars and current:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return "\n".join(lines)
