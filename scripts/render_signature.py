#!/usr/bin/env python3
"""Render exact signature text as a transparent pencil/pen-style bitmap."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont


DEFAULT_TEXT = "XRWRX"
USER_FONTS = Path.home() / "Library" / "Fonts"
FONT_CANDIDATES = (
    USER_FONTS / "ELEYANG-Student-Light.ttf",
    USER_FONTS / "ELEYANG-Soft-Light.ttf",
    USER_FONTS / "江西拙楷2.0.ttf",
    Path("/System/Library/Fonts/STHeiti Medium.ttc"),
    Path("/System/Library/Fonts/PingFang.ttc"),
    Path("/Library/Fonts/Arial Unicode.ttf"),
    Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    Path("C:/Windows/Fonts/msyh.ttc"),
    Path("C:/Windows/Fonts/arial.ttf"),
)


def resolve_font(font_path: Path | None) -> Path:
    if font_path:
        if not font_path.exists():
            raise FileNotFoundError(f"signature font not found: {font_path}")
        return font_path
    for candidate in FONT_CANDIDATES:
        if candidate.exists():
            return candidate
    raise FileNotFoundError("no Chinese-capable signature font was found")


def render_signature(
    text: str,
    font_path: Path | None = None,
    font_size: int = 132,
    color: tuple[int, int, int] = (45, 45, 45),
    seed: int = 17,
) -> Image.Image:
    text = text or DEFAULT_TEXT
    font = ImageFont.truetype(str(resolve_font(font_path)), font_size)
    scratch = Image.new("L", (2400, 600), 0)
    draw = ImageDraw.Draw(scratch)
    bbox = draw.textbbox((0, 0), text, font=font, stroke_width=0)
    x = 80 - bbox[0]
    y = 80 - bbox[1]
    draw.text((x, y), text, fill=238, font=font)

    mask = np.asarray(scratch, dtype=np.float32)
    rng = np.random.default_rng(seed)
    grain = rng.normal(loc=0.95, scale=0.055, size=mask.shape)
    alpha = np.clip(mask * grain, 0, 255)
    dropout = rng.random(mask.shape) < 0.008
    alpha[dropout & (mask > 20)] *= rng.uniform(0.15, 0.6)
    alpha = alpha.astype(np.uint8)

    ys, xs = np.where(alpha > 4)
    if len(xs) == 0:
        raise RuntimeError("signature text produced an empty mask")
    pad = max(8, font_size // 15)
    left = max(0, int(xs.min()) - pad)
    top = max(0, int(ys.min()) - pad)
    right = min(alpha.shape[1], int(xs.max()) + pad + 1)
    bottom = min(alpha.shape[0], int(ys.max()) + pad + 1)
    cropped_alpha = alpha[top:bottom, left:right]

    rgba = np.zeros((cropped_alpha.shape[0], cropped_alpha.shape[1], 4), dtype=np.uint8)
    rgba[..., 0] = color[0]
    rgba[..., 1] = color[1]
    rgba[..., 2] = color[2]
    rgba[..., 3] = cropped_alpha
    return Image.fromarray(rgba, "RGBA")


def main() -> None:
    parser = argparse.ArgumentParser(description="Render an exact handwritten signature PNG.")
    parser.add_argument("--text", default=DEFAULT_TEXT)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--font", type=Path)
    parser.add_argument("--font-size", type=int, default=132)
    parser.add_argument("--color", default="#2D2D2D")
    parser.add_argument("--seed", type=int, default=17)
    args = parser.parse_args()

    value = args.color.lstrip("#")
    if len(value) != 6:
        raise SystemExit("color must be a six-digit hex value")
    color = tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))
    image = render_signature(args.text, args.font, args.font_size, color, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    image.save(args.output)
    print(f"saved={args.output} size={image.width}x{image.height} text={args.text}")


if __name__ == "__main__":
    main()
