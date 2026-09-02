"""Parses free-text edit requests ("Pedir à IA") into a fixed, whitelisted action.

Rule-based first (fast, deterministic, works with zero extra installs). If no
rule matches and a local Ollama server is available, the model is asked to
pick one of the *same* whitelisted actions and return JSON — its output is
never executed as code, only mapped through this fixed action set, so a
model hallucination can at worst produce "unknown".
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from backend.app import llm

VALID_ACTIONS = {
    "remove_music",
    "strengthen_hook",
    "speed_up",
    "slow_down",
    "set_caption_style",
    "unknown",
}

VALID_STYLES = {"discreto", "editorial", "impacto", "karaoke", "uma_palavra", "manuscrito"}


@dataclass
class AssistantAction:
    action: str
    params: Dict[str, Any] = field(default_factory=dict)
    message: str = ""


_RULES: List[tuple] = [
    (re.compile(r"tira(r)? a m[uú]sica|remove(r)? a m[uú]sica|sem m[uú]sica"),
     "remove_music", "Removi a música do vídeo."),
    (re.compile(r"gancho (mais|maior) (forte|impactante)|gancho mais forte"),
     "strengthen_hook", "Gerei um gancho mais forte para a abertura."),
    (re.compile(r"acelera(r)?|mais r[aá]pido"),
     "speed_up", "Aumentei ligeiramente a velocidade."),
    (re.compile(r"abranda(r)?|mais lento|diminui(r)? (a )?velocidade"),
     "slow_down", "Reduzi ligeiramente a velocidade."),
]

_STYLE_RULE = re.compile(
    r"estilo (discreto|editorial|impacto|karaoke|uma palavra|manuscrito)"
)


def _match_rules(lower: str) -> Optional[AssistantAction]:
    style_match = _STYLE_RULE.search(lower)
    if style_match:
        style = style_match.group(1).replace(" ", "_")
        return AssistantAction(
            action="set_caption_style", params={"style": style},
            message=f"Mudei o estilo de legenda para {style_match.group(1)}.",
        )
    for pattern, action, message in _RULES:
        if pattern.search(lower):
            return AssistantAction(action=action, params={}, message=message)
    return None


def _ask_llm(text: str) -> Optional[AssistantAction]:
    if not llm.is_available():
        return None
    prompt = (
        "Converte o pedido do utilizador numa ação JSON com as chaves \"action\" "
        f"(uma de {sorted(VALID_ACTIONS)}), \"params\" (objeto; para "
        "set_caption_style inclui {\"style\": uma de "
        f"{sorted(VALID_STYLES)}}}) e \"message\" (frase curta em português "
        f"confirmando a ação). Pedido: {text!r}. Responde só com o JSON."
    )
    raw = llm.generate(prompt)
    if not raw:
        return None
    try:
        start, end = raw.index("{"), raw.rindex("}") + 1
        data = json.loads(raw[start:end])
    except (ValueError, json.JSONDecodeError):
        return None

    action = data.get("action")
    if action not in VALID_ACTIONS:
        return None
    params = data.get("params") or {}
    if action == "set_caption_style" and params.get("style") not in VALID_STYLES:
        return None
    return AssistantAction(action=action, params=params, message=str(data.get("message", "")))


def parse_command(text: str) -> AssistantAction:
    lower = text.lower()

    rule_match = _match_rules(lower)
    if rule_match:
        return rule_match

    llm_match = _ask_llm(text)
    if llm_match:
        return llm_match

    return AssistantAction(
        action="unknown",
        params={},
        message="Não percebi bem o pedido. Tenta algo como 'tira a música', 'gancho mais forte' ou 'estilo karaoke'.",
    )
