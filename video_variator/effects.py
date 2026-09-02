"""Builds and runs the ffmpeg filter graph for one video variation.

Every variation combines four small, independently randomized edits: playback
speed, color (brightness/contrast/saturation/hue), a subtle zoom/crop, and a
title caption drawn in a box near the top of the frame.
"""
from __future__ import annotations

import random
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

from .titles import wrap_text

DEFAULT_FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]


def find_default_font() -> Optional[str]:
    for candidate in DEFAULT_FONT_CANDIDATES:
        if Path(candidate).exists():
            return candidate
    return None


def probe_video_height(input_path: str) -> Optional[int]:
    if not shutil.which("ffprobe"):
        return None
    try:
        out = subprocess.run(
            [
                "ffprobe", "-v", "error", "-select_streams", "v:0",
                "-show_entries", "stream=height", "-of", "csv=p=0", input_path,
            ],
            capture_output=True, text=True, check=True,
        )
        return int(out.stdout.strip())
    except (subprocess.CalledProcessError, ValueError):
        return None


@dataclass
class VariationParams:
    title: str
    speed: float
    brightness: float
    contrast: float
    saturation: float
    hue_deg: float
    crop_fraction: float
    mirror: bool


def random_variation_params(
    rng: random.Random,
    title: str,
    *,
    speed_range: Tuple[float, float] = (0.96, 1.06),
    brightness_range: Tuple[float, float] = (-0.03, 0.03),
    contrast_range: Tuple[float, float] = (0.95, 1.05),
    saturation_range: Tuple[float, float] = (0.9, 1.1),
    hue_range: Tuple[float, float] = (-6.0, 6.0),
    crop_range: Tuple[float, float] = (0.0, 0.03),
    allow_mirror: bool = False,
) -> VariationParams:
    return VariationParams(
        title=title,
        speed=rng.uniform(*speed_range),
        brightness=rng.uniform(*brightness_range),
        contrast=rng.uniform(*contrast_range),
        saturation=rng.uniform(*saturation_range),
        hue_deg=rng.uniform(*hue_range),
        crop_fraction=rng.uniform(*crop_range),
        mirror=allow_mirror and rng.random() < 0.5,
    )


def _escape_ffmpeg_path(path: str) -> str:
    escaped = path.replace("\\", "\\\\").replace("'", "\\'")
    return f"'{escaped}'"


def _clamp_atempo(speed: float) -> float:
    return min(2.0, max(0.5, speed))


def build_filter_complex(
    params: VariationParams, *, font_path: str, fontsize: int, textfile: str
) -> str:
    video_filters = []
    if params.crop_fraction > 0:
        keep = 1 - params.crop_fraction
        video_filters.append(f"crop=iw*{keep:.4f}:ih*{keep:.4f},scale=iw/{keep:.4f}:ih/{keep:.4f}")
    if params.mirror:
        video_filters.append("hflip")
    video_filters.append(
        f"eq=brightness={params.brightness:.4f}:contrast={params.contrast:.4f}:"
        f"saturation={params.saturation:.4f}"
    )
    video_filters.append(f"hue=h={params.hue_deg:.2f}")
    video_filters.append(f"setpts=PTS/{params.speed:.5f}")
    video_filters.append(
        "drawtext=fontfile={font}:textfile={textfile}:fontcolor=white:fontsize={size}:"
        "box=1:boxcolor=black@0.55:boxborderw=18:x=(w-text_w)/2:y=h*0.06:line_spacing=6".format(
            font=_escape_ffmpeg_path(font_path),
            textfile=_escape_ffmpeg_path(textfile),
            size=fontsize,
        )
    )
    video_chain = ",".join(video_filters)
    audio_chain = f"atempo={_clamp_atempo(params.speed):.5f}"
    return f"[0:v]{video_chain}[v];[0:a]{audio_chain}[a]"


def render_variation(
    input_path: str,
    output_path: str,
    params: VariationParams,
    *,
    font_path: str,
    fontsize: int,
) -> None:
    if not shutil.which("ffmpeg"):
        raise RuntimeError("ffmpeg não encontrado no PATH. Instala o ffmpeg para gerar os vídeos.")

    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as tf:
        tf.write(wrap_text(params.title))
        textfile = tf.name

    try:
        filter_complex = build_filter_complex(
            params, font_path=font_path, fontsize=fontsize, textfile=textfile
        )
        cmd = [
            "ffmpeg", "-y", "-i", input_path,
            "-filter_complex", filter_complex,
            "-map", "[v]", "-map", "[a]",
            "-c:v", "libx264", "-preset", "medium", "-crf", "20",
            "-c:a", "aac", "-b:a", "160k",
            output_path,
        ]
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"ffmpeg falhou a gerar {output_path}:\n{exc.stderr}") from exc
    finally:
        Path(textfile).unlink(missing_ok=True)
