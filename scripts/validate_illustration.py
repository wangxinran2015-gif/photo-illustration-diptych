#!/usr/bin/env python3
"""Validate ratio, paper background, and optional Asian skin base color."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps


BG = np.array([253, 252, 252], dtype=np.float32)
SKIN = np.array([255, 241, 223], dtype=np.float32)


def border_pixels(rgb: np.ndarray, fraction: float = 0.05) -> np.ndarray:
    height, width, _ = rgb.shape
    band_y = max(1, int(round(height * fraction)))
    band_x = max(1, int(round(width * fraction)))
    return np.concatenate(
        [
            rgb[:band_y].reshape(-1, 3),
            rgb[-band_y:].reshape(-1, 3),
            rgb[:, :band_x].reshape(-1, 3),
            rgb[:, -band_x:].reshape(-1, 3),
        ],
        axis=0,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate a generated 3:4 illustration.")
    parser.add_argument("--image", required=True, type=Path)
    parser.add_argument("--expect-asian-skin", action="store_true")
    parser.add_argument("--background-tolerance", type=float, default=14.0)
    parser.add_argument("--skin-tolerance", type=float, default=12.0)
    parser.add_argument("--minimum-skin-coverage", type=float, default=0.003)
    args = parser.parse_args()

    with Image.open(args.image) as opened:
        image = ImageOps.exif_transpose(opened).convert("RGB")
    rgb = np.asarray(image, dtype=np.float32)

    ratio = image.width / image.height
    ratio_ok = abs(ratio - 0.75) <= 0.015

    border = border_pixels(rgb)
    border_median = np.median(border, axis=0)
    background_delta = float(np.linalg.norm(border_median - BG))
    background_ok = background_delta <= args.background_tolerance

    skin_delta = np.linalg.norm(rgb - SKIN, axis=2)
    skin_coverage = float(np.mean(skin_delta <= args.skin_tolerance))
    skin_ok = (
        not args.expect_asian_skin
        or skin_coverage >= args.minimum_skin_coverage
    )

    report = {
        "image": str(args.image),
        "size": [image.width, image.height],
        "ratio": round(ratio, 6),
        "ratio_ok": ratio_ok,
        "background_border_median": [round(float(v), 2) for v in border_median],
        "background_delta": round(background_delta, 3),
        "background_ok": background_ok,
        "expected_skin": "#FFF1DF" if args.expect_asian_skin else None,
        "skin_coverage_within_tolerance": round(skin_coverage, 6),
        "skin_ok": skin_ok,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not (ratio_ok and background_ok and skin_ok):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
