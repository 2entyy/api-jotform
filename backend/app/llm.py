"""Optional local LLM enrichment via Ollama (http://localhost:11434).

Everything in this app works without this: when Ollama isn't running, callers
fall back to the heuristic critic/assistant. No API key, no network call ever
leaves the machine — this only talks to localhost.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Optional

OLLAMA_TAGS_URL = "http://localhost:11434/api/tags"
OLLAMA_GENERATE_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "llama3.1"


def is_available(timeout: float = 0.5) -> bool:
    try:
        urllib.request.urlopen(OLLAMA_TAGS_URL, timeout=timeout)
        return True
    except (urllib.error.URLError, OSError, TimeoutError):
        return False


def generate(prompt: str, model: str = DEFAULT_MODEL, timeout: float = 20.0) -> Optional[str]:
    payload = json.dumps({"model": model, "prompt": prompt, "stream": False}).encode("utf-8")
    req = urllib.request.Request(
        OLLAMA_GENERATE_URL, data=payload, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("response")
    except (urllib.error.URLError, OSError, TimeoutError, json.JSONDecodeError):
        return None
