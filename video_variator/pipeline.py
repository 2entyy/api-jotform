"""End-to-end orchestration: transcribe once, then render N distinct variations."""
from __future__ import annotations

import json
import random
from dataclasses import asdict
from pathlib import Path
from typing import Optional

from .effects import find_default_font, probe_video_height, random_variation_params, render_variation
from .titles import generate_titles
from .transcribe import transcribe


def run(
    input_path: str,
    output_dir: str,
    *,
    num_variations: int = 5,
    model_size: str = "small",
    seed: Optional[int] = None,
    font_path: Optional[str] = None,
    fontsize: Optional[int] = None,
    allow_mirror: bool = False,
    allow_crop: bool = True,
    dry_run: bool = False,
) -> dict:
    input_path = str(Path(input_path))
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    transcript = transcribe(input_path, model_size=model_size)
    titles = generate_titles(transcript.text, transcript.language, num_variations, seed=seed)

    font = font_path or find_default_font()
    if not font and not dry_run:
        raise RuntimeError(
            "Nenhuma fonte encontrada. Instala uma fonte (ex: fonts-dejavu-core) ou passa "
            "--font /caminho/para/fonte.ttf"
        )

    height = probe_video_height(input_path)
    default_fontsize = max(28, int((height or 720) * 0.06))

    rng = random.Random(seed)
    stem = Path(input_path).stem
    crop_range = (0.0, 0.03) if allow_crop else (0.0, 0.0)

    manifest: dict = {
        "source": input_path,
        "language": transcript.language,
        "transcript": transcript.text,
        "variations": [],
    }

    for i, title in enumerate(titles, start=1):
        params = random_variation_params(
            rng, title, allow_mirror=allow_mirror, crop_range=crop_range
        )
        out_name = f"{stem}_var{i}.mp4"
        out_path = out_dir / out_name
        manifest["variations"].append({"file": out_name, **asdict(params)})

        if not dry_run:
            render_variation(
                input_path,
                str(out_path),
                params,
                font_path=font,
                fontsize=fontsize or default_fontsize,
            )

    manifest_path = out_dir / f"{stem}_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    manifest["manifest_path"] = str(manifest_path)
    return manifest
