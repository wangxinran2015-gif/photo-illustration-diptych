#!/usr/bin/env python3
"""Add an exact signature to an illustration and join it with a 3:4 photo."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps

from render_signature import DEFAULT_TEXT, render_signature


BG_COLOR = (253, 252, 252)
POSITIONS = ("bottom-right", "top-right", "bottom-left", "top-left")


def load_panel(path: Path, size: tuple[int, int], pad: bool) -> Image.Image:
    with Image.open(path) as opened:
        image = ImageOps.exif_transpose(opened).convert("RGBA")
    if pad:
        return ImageOps.pad(
            image,
            size,
            method=Image.Resampling.LANCZOS,
            color=BG_COLOR + (255,),
            centering=(0.5, 0.5),
        )
    return ImageOps.fit(image, size, method=Image.Resampling.LANCZOS)


def tint_signature(signature: Image.Image, color: tuple[int, int, int]) -> Image.Image:
    rgba = np.asarray(signature.convert("RGBA"), dtype=np.uint8).copy()
    rgba[..., 0] = color[0]
    rgba[..., 1] = color[1]
    rgba[..., 2] = color[2]
    return Image.fromarray(rgba, "RGBA")


def sample_dark_color(image: Image.Image) -> tuple[int, int, int]:
    rgb = np.asarray(image.convert("RGB"), dtype=np.int16)
    delta = np.linalg.norm(rgb - np.array(BG_COLOR, dtype=np.int16), axis=2)
    subject = rgb[delta > 18]
    if len(subject) == 0:
        return 45, 45, 45
    luminance = subject @ np.array([0.2126, 0.7152, 0.0722])
    dark = int(np.percentile(luminance, 12))
    dark = max(24, min(72, dark))
    return dark, dark, dark


def placement_box(
    position: str,
    canvas_size: tuple[int, int],
    signature_size: tuple[int, int],
    margin: int,
) -> tuple[int, int, int, int]:
    width, height = canvas_size
    sig_w, sig_h = signature_size
    left = width - margin - sig_w if position.endswith("right") else margin
    top = height - margin - sig_h if position.startswith("bottom") else margin
    return left, top, left + sig_w, top + sig_h


def blankness_score(image: Image.Image, box: tuple[int, int, int, int]) -> float:
    region = np.asarray(image.crop(box).convert("RGB"), dtype=np.float32)
    delta = np.linalg.norm(region - np.array(BG_COLOR, dtype=np.float32), axis=2)
    occupied = np.mean(delta > 20)
    return float(occupied + np.mean(np.clip(delta / 255.0, 0, 1)) * 0.25)


def choose_position(
    image: Image.Image,
    signature_size: tuple[int, int],
    margin: int,
    requested: str,
) -> tuple[str, tuple[int, int, int, int]]:
    choices = POSITIONS if requested == "auto" else (requested,)
    scored = []
    for position in choices:
        box = placement_box(position, image.size, signature_size, margin)
        scored.append((blankness_score(image, box), position, box))
    _, position, box = min(scored, key=lambda item: item[0])
    return position, box


def save_image(image: Image.Image, output: Path, quality: int) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.suffix.lower() in {".jpg", ".jpeg"}:
        image.convert("RGB").save(output, quality=quality, subsampling=0, optimize=True)
    else:
        image.save(output)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sign a 3:4 illustration and join it to the right of a 3:4 photo."
    )
    parser.add_argument("--photo", required=True, type=Path)
    parser.add_argument("--illustration", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--signed-illustration-out", type=Path)
    parser.add_argument("--signature-text", default=DEFAULT_TEXT)
    parser.add_argument("--signature-image", type=Path)
    parser.add_argument("--signature-font", type=Path)
    parser.add_argument(
        "--signature-position",
        choices=("auto",) + POSITIONS,
        default="auto",
    )
    parser.add_argument("--signature-width", type=float, default=0.17)
    parser.add_argument("--margin", type=float, default=0.05)
    parser.add_argument("--panel-width", type=int, default=768)
    parser.add_argument("--panel-height", type=int, default=1024)
    parser.add_argument("--gutter", type=int, default=0)
    parser.add_argument("--quality", type=int, default=95)
    args = parser.parse_args()

    if abs(args.panel_width / args.panel_height - 0.75) > 1e-6:
        raise SystemExit("panel dimensions must use a 3:4 ratio")
    if not 0.08 <= args.signature_width <= 0.25:
        raise SystemExit("signature-width must be between 0.08 and 0.25")
    if not 0.02 <= args.margin <= 0.12:
        raise SystemExit("margin must be between 0.02 and 0.12")

    panel_size = (args.panel_width, args.panel_height)
    photo = load_panel(args.photo, panel_size, pad=False).convert("RGB")
    illustration = load_panel(args.illustration, panel_size, pad=True)

    if args.signature_image:
        with Image.open(args.signature_image) as opened:
            signature = opened.convert("RGBA")
    else:
        default_asset = (
            Path(__file__).resolve().parent.parent / "assets" / "default-signature.png"
        )
        if args.signature_text == DEFAULT_TEXT and default_asset.exists():
            with Image.open(default_asset) as opened:
                signature = opened.convert("RGBA")
        else:
            signature = render_signature(args.signature_text, args.signature_font)

    target_w = max(1, int(round(args.panel_width * args.signature_width)))
    target_h = max(1, int(round(signature.height * target_w / signature.width)))
    signature = signature.resize((target_w, target_h), Image.Resampling.LANCZOS)
    signature = tint_signature(signature, sample_dark_color(illustration))

    margin_px = int(round(args.panel_width * args.margin))
    position, box = choose_position(
        illustration, signature.size, margin_px, args.signature_position
    )
    illustration.alpha_composite(signature, dest=(box[0], box[1]))

    if args.signed_illustration_out:
        save_image(illustration, args.signed_illustration_out, args.quality)

    final_width = args.panel_width * 2 + args.gutter
    final = Image.new("RGB", (final_width, args.panel_height), BG_COLOR)
    final.paste(photo, (0, 0))
    final.paste(illustration.convert("RGB"), (args.panel_width + args.gutter, 0))
    save_image(final, args.output, args.quality)
    print(
        f"saved={args.output} size={final.width}x{final.height} "
        f"signature={args.signature_text!r} position={position} box={box}"
    )


if __name__ == "__main__":
    main()

