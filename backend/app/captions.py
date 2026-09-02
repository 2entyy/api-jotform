"""Builds .ass subtitle files for each caption style preset.

ASS (Advanced SubStation Alpha) is used instead of plain drawtext because it
gives per-style fonts/colors/positioning and, for the word-driven styles
(Karaoke, Uma palavra), per-word timing via \\k karaoke tags — something
drawtext cannot do on its own.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from backend.app.schemas import Segment


@dataclass(frozen=True)
class StyleSpec:
    key: str
    label: str
    font: str
    fontsize_ratio: float
    primary_color: str
    highlight_color: str
    outline_color: str
    back_color: str
    bold: bool
    italic: bool
    alignment: int
    margin_v_ratio: float
    mode: str  # "line" | "word" | "one_word"
    uppercase: bool = False


# ASS colours are &HAABBGGRR (alpha, blue, green, red); 00 alpha = opaque.
STYLES: Dict[str, StyleSpec] = {
    "discreto": StyleSpec(
        "discreto", "Discreto", "DejaVu Sans", 0.035,
        "&H00FFFFFF", "&H00FFFFFF", "&H00000000", "&H80000000",
        False, False, 2, 0.06, "line",
    ),
    "editorial": StyleSpec(
        "editorial", "Editorial", "DejaVu Serif", 0.045,
        "&H00FFFFFF", "&H00FFFFFF", "&H00000000", "&H00000000",
        True, False, 2, 0.08, "line",
    ),
    "impacto": StyleSpec(
        "impacto", "Impacto", "DejaVu Sans", 0.07,
        "&H0000FFFF", "&H0000FFFF", "&H00000000", "&H00000000",
        True, False, 8, 0.06, "line", uppercase=True,
    ),
    "karaoke": StyleSpec(
        "karaoke", "Karaoke", "DejaVu Sans", 0.06,
        "&H00FFFFFF", "&H0000FFFF", "&H00000000", "&H00000000",
        True, False, 2, 0.1, "word",
    ),
    "uma_palavra": StyleSpec(
        "uma_palavra", "Uma palavra", "DejaVu Sans", 0.11,
        "&H00FFFFFF", "&H0000FFFF", "&H00000000", "&H00000000",
        True, False, 5, 0.0, "one_word", uppercase=True,
    ),
    "manuscrito": StyleSpec(
        "manuscrito", "Manuscrito", "DejaVu Sans", 0.05,
        "&H00E6C9FF", "&H00E6C9FF", "&H00000000", "&H00000000",
        False, True, 2, 0.1, "line",
    ),
}

STYLE_ORDER = ["discreto", "editorial", "impacto", "karaoke", "uma_palavra", "manuscrito"]


def _ass_time(t: float) -> str:
    t = max(0.0, t)
    cs = round(t * 100)
    h, rem = divmod(cs, 360000)
    m, rem = divmod(rem, 6000)
    s, cs = divmod(rem, 100)
    return f"{h:d}:{m:02d}:{s:02d}.{cs:02d}"


def _escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("{", "(").replace("}", ")").replace("\n", "\\N")


def _header(style: StyleSpec, video_w: int, video_h: int) -> str:
    fontsize = max(18, int(video_h * style.fontsize_ratio))
    margin_v = int(video_h * style.margin_v_ratio)
    bold = -1 if style.bold else 0
    italic = -1 if style.italic else 0
    return (
        "[Script Info]\n"
        "ScriptType: v4.00+\n"
        f"PlayResX: {video_w}\n"
        f"PlayResY: {video_h}\n"
        "WrapStyle: 1\n"
        "ScaledBorderAndShadow: yes\n\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, "
        "BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, "
        "BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        f"Style: Default,{style.font},{fontsize},{style.primary_color},{style.highlight_color},"
        f"{style.outline_color},{style.back_color},{bold},{italic},0,0,100,100,0,0,1,3,0,"
        f"{style.alignment},20,20,{margin_v},1\n\n"
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )


def build_ass(segments: List[Segment], style_key: str, video_w: int, video_h: int) -> str:
    style = STYLES.get(style_key, STYLES["impacto"])
    lines = [_header(style, video_w, video_h)]

    for seg in segments:
        if style.mode == "word" and seg.words:
            parts = []
            for w in seg.words:
                dur_cs = max(1, round((w.end - w.start) * 100))
                word = w.word.upper() if style.uppercase else w.word
                parts.append(f"{{\\k{dur_cs}}}{_escape(word)}")
            text = " ".join(parts)
            lines.append(f"Dialogue: 0,{_ass_time(seg.start)},{_ass_time(seg.end)},Default,,0,0,0,,{text}")
        elif style.mode == "one_word" and seg.words:
            for w in seg.words:
                word = w.word.upper() if style.uppercase else w.word
                lines.append(
                    f"Dialogue: 0,{_ass_time(w.start)},{_ass_time(w.end)},Default,,0,0,0,,{_escape(word)}"
                )
        else:
            text = seg.text.upper() if style.uppercase else seg.text
            lines.append(
                f"Dialogue: 0,{_ass_time(seg.start)},{_ass_time(seg.end)},Default,,0,0,0,,{_escape(text)}"
            )

    return "\n".join(lines) + "\n"
