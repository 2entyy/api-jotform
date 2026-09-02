"""Builds and runs the ffmpeg commands: full render and fast style-preview clips."""
from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple

from backend.app.captions import STYLES, build_ass
from backend.app.music import build_duck_filter
from backend.app.schemas import Project, Segment

DEFAULT_FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]


def find_default_font() -> Optional[str]:
    for candidate in DEFAULT_FONT_CANDIDATES:
        if Path(candidate).exists():
            return candidate
    return None


def _escape_ffmpeg_path(path: str) -> str:
    escaped = str(path).replace("\\", "\\\\").replace("'", "\\'").replace(":", "\\:")
    return f"'{escaped}'"


def probe_dimensions(input_path: str) -> Tuple[int, int]:
    if not shutil.which("ffprobe"):
        return 1080, 1920
    try:
        out = subprocess.run(
            [
                "ffprobe", "-v", "error", "-select_streams", "v:0",
                "-show_entries", "stream=width,height", "-of", "csv=p=0:s=x", input_path,
            ],
            capture_output=True, text=True, check=True,
        )
        w, h = out.stdout.strip().split("x")
        return int(w), int(h)
    except Exception:
        return 1080, 1920


def _hook_drawtext(hook_text: str, video_h: int, font_path: str, start: float, end: float) -> Tuple[str, str]:
    fontsize = max(24, int(video_h * 0.07))
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as tf:
        tf.write(hook_text.upper())
        textfile = tf.name
    filt = (
        f"drawtext=fontfile={_escape_ffmpeg_path(font_path)}:textfile={_escape_ffmpeg_path(textfile)}:"
        f"fontcolor=white:fontsize={fontsize}:box=1:boxcolor=black@0.55:boxborderw=18:"
        f"x=(w-text_w)/2:y=h*0.05:line_spacing=6:enable='between(t,{start},{end})'"
    )
    return filt, textfile


def _run(cmd: List[str]) -> None:
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"ffmpeg falhou: {exc.stderr}") from exc


def render_project(
    project: Project,
    input_path: str,
    output_path: str,
    *,
    font_path: str,
    music_path: Optional[str] = None,
) -> None:
    if not shutil.which("ffmpeg"):
        raise RuntimeError("ffmpeg não encontrado no PATH.")

    width, height = probe_dimensions(input_path)
    ass_text = build_ass(project.segments, project.caption_style, width, height)
    with tempfile.NamedTemporaryFile("w", suffix=".ass", delete=False, encoding="utf-8") as tf:
        tf.write(ass_text)
        ass_path = tf.name

    temp_files = [ass_path]
    trim_start = project.trim.start or 0.0
    trim_end = project.trim.end

    video_filters = []
    if trim_end:
        video_filters.append(f"trim=start={trim_start}:end={trim_end},setpts=PTS-STARTPTS")
    elif trim_start:
        video_filters.append(f"trim=start={trim_start},setpts=PTS-STARTPTS")

    video_filters.append(f"subtitles={_escape_ffmpeg_path(ass_path)}")

    if project.hook and project.hook.text:
        hook_filter, hook_textfile = _hook_drawtext(
            project.hook.text, height, font_path, project.hook.start, project.hook.end
        )
        temp_files.append(hook_textfile)
        video_filters.append(hook_filter)

    speed = project.speed or 1.0
    if abs(speed - 1.0) > 1e-6:
        video_filters.append(f"setpts=PTS/{speed:.5f}")

    video_chain = ",".join(video_filters)
    filter_complex_parts = [f"[0:v]{video_chain}[v]"]
    maps = ["-map", "[v]"]

    atempo = min(2.0, max(0.5, speed))
    voice_chain = f"atempo={atempo:.5f}" if abs(speed - 1.0) > 1e-6 else "anull"

    if music_path:
        duck = build_duck_filter(project.segments, project.music.duck_level)
        filter_complex_parts.append(f"[0:a]{voice_chain}[voice]")
        filter_complex_parts.append(f"[1:a]{duck},volume={project.music.volume}[music]")
        filter_complex_parts.append("[voice][music]amix=inputs=2:duration=first:dropout_transition=2[a]")
        inputs = ["-i", input_path, "-i", music_path]
    else:
        filter_complex_parts.append(f"[0:a]{voice_chain}[a]")
        inputs = ["-i", input_path]
    maps += ["-map", "[a]"]

    filter_complex = ";".join(filter_complex_parts)
    cmd = [
        "ffmpeg", "-y", *inputs,
        "-filter_complex", filter_complex, *maps,
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-c:a", "aac", "-b:a", "160k",
        output_path,
    ]

    try:
        _run(cmd)
    finally:
        for f in temp_files:
            Path(f).unlink(missing_ok=True)


def render_micro_variation(input_path: str, output_path: str, params) -> None:
    """Applies only the speed/color/crop/mirror tweaks (no drawtext) — used to
    generate several near-duplicate exports of an already-approved render, for
    reels A/B testing. `params` is a `video_variator.effects.VariationParams`."""
    if not shutil.which("ffmpeg"):
        raise RuntimeError("ffmpeg não encontrado no PATH.")

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
    video_chain = ",".join(video_filters)

    atempo = min(2.0, max(0.5, params.speed))
    filter_complex = f"[0:v]{video_chain}[v];[0:a]atempo={atempo:.5f}[a]"

    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-filter_complex", filter_complex,
        "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-c:a", "aac", "-b:a", "160k",
        output_path,
    ]
    _run(cmd)


def render_style_preview(
    input_path: str,
    output_path: str,
    segments: List[Segment],
    style_key: str,
    *,
    duration: float = 4.0,
) -> None:
    if not shutil.which("ffmpeg"):
        raise RuntimeError("ffmpeg não encontrado no PATH.")
    if style_key not in STYLES:
        raise ValueError(f"Estilo desconhecido: {style_key}")

    width, height = probe_dimensions(input_path)
    preview_h = 480
    preview_w = int(width * preview_h / height) if height else 270
    windowed = [s for s in segments if s.start < duration]
    ass_text = build_ass(windowed, style_key, preview_w, preview_h)

    with tempfile.NamedTemporaryFile("w", suffix=".ass", delete=False, encoding="utf-8") as tf:
        tf.write(ass_text)
        ass_path = tf.name

    try:
        cmd = [
            "ffmpeg", "-y", "-i", input_path, "-t", str(duration),
            "-vf", f"scale={preview_w}:{preview_h},subtitles={_escape_ffmpeg_path(ass_path)}",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "28",
            "-an", output_path,
        ]
        _run(cmd)
    finally:
        Path(ass_path).unlink(missing_ok=True)
