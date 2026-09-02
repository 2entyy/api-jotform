"""Command-line entry point: `python -m video_variator.cli video.mp4 -n 5 -o output`."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional

from .pipeline import run


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="video-variator",
        description=(
            "Gera várias variações subtis de um vídeo base (legenda com título sugerido, "
            "velocidade, cor e micro-zoom) para testar em Reels."
        ),
    )
    parser.add_argument("input", help="Caminho para o vídeo base")
    parser.add_argument("-o", "--output-dir", default="output", help="Pasta de saída das variações")
    parser.add_argument("-n", "--num-variations", type=int, default=5, help="Número de variações a gerar")
    parser.add_argument(
        "--model", default="small", choices=["tiny", "base", "small", "medium", "large"],
        help="Tamanho do modelo Whisper local (maior = mais preciso, mais lento)",
    )
    parser.add_argument("--seed", type=int, default=None, help="Seed para resultados reprodutíveis")
    parser.add_argument("--font", default=None, help="Caminho para uma fonte .ttf para o título")
    parser.add_argument("--fontsize", type=int, default=None, help="Tamanho de fonte fixo (px)")
    parser.add_argument(
        "--allow-mirror", action="store_true",
        help="Permitir espelhar (flip horizontal) como variação possível",
    )
    parser.add_argument(
        "--no-crop", action="store_true", help="Desativar o micro-zoom/crop subtil"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Só transcreve e escreve o manifest.json, sem renderizar vídeo",
    )
    args = parser.parse_args(argv)

    manifest = run(
        args.input,
        args.output_dir,
        num_variations=args.num_variations,
        model_size=args.model,
        seed=args.seed,
        font_path=args.font,
        fontsize=args.fontsize,
        allow_mirror=args.allow_mirror,
        allow_crop=not args.no_crop,
        dry_run=args.dry_run,
    )
    print(json.dumps(
        {"manifest": manifest.get("manifest_path"), "variacoes": len(manifest["variations"])},
        indent=2, ensure_ascii=False,
    ))
    return 0


if __name__ == "__main__":
    sys.exit(main())
