#!/usr/bin/env python3
"""Create a deterministic subject-focused 3:4 crop from an uploaded photo."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageOps


TARGET_RATIO = 3 / 4


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def crop_box_for_focus(
    width: int, height: int, focus_x: float, focus_y: float
) -> tuple[int, int, int, int]:
    """Return a maximal 3:4 crop centered as closely as possible on the focus."""
    source_ratio = width / height
    focus_px_x = clamp(focus_x, 0.0, 1.0) * width
    focus_px_y = clamp(focus_y, 0.0, 1.0) * height

    if source_ratio > TARGET_RATIO:
        crop_h = height
        crop_w = int(round(crop_h * TARGET_RATIO))
        left = int(round(focus_px_x - crop_w / 2))
        left = max(0, min(width - crop_w, left))
        top = 0
    else:
        crop_w = width
        crop_h = int(round(crop_w / TARGET_RATIO))
        top = int(round(focus_px_y - crop_h / 2))
        top = max(0, min(height - crop_h, top))
        left = 0

    return left, top, left + crop_w, top + crop_h


def save_image(image: Image.Image, output: Path, quality: int) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    suffix = output.suffix.lower()
    if suffix in {".jpg", ".jpeg"}:
        image.convert("RGB").save(output, quality=quality, subsampling=0, optimize=True)
    else:
        image.save(output)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Crop one photo to 3:4 around a normalized focus point."
    )
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--focus-x", type=float, default=0.5)
    parser.add_argument("--focus-y", type=float, default=0.5)
    parser.add_argument("--width", type=int, default=768)
    parser.add_argument("--height", type=int, default=1024)
    parser.add_argument("--quality", type=int, default=95)
    args = parser.parse_args()

    if args.width <= 0 or args.height <= 0:
        raise SystemExit("width and height must be positive")
    if abs(args.width / args.height - TARGET_RATIO) > 1e-6:
        raise SystemExit("output width and height must use a 3:4 ratio")

    with Image.open(args.input) as opened:
        photo = ImageOps.exif_transpose(opened).convert("RGB")
    crop_box = crop_box_for_focus(
        photo.width, photo.height, args.focus_x, args.focus_y
    )
    cropped = photo.crop(crop_box).resize(
        (args.width, args.height), Image.Resampling.LANCZOS
    )
    save_image(cropped, args.output, args.quality)
    print(
        f"saved={args.output} size={cropped.width}x{cropped.height} "
        f"crop={crop_box} focus=({args.focus_x:.3f},{args.focus_y:.3f})"
    )


if __name__ == "__main__":
    main()

