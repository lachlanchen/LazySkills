#!/usr/bin/env python3
"""Export approved album artwork to platform sizes without altering GIF animation."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

from PIL import Image, ImageOps


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fitted(image, size, color=(0, 0, 0, 0), margin=0):
    canvas = Image.new("RGBA", size, color)
    inner = (size[0] - margin * 2, size[1] - margin * 2)
    thumb = ImageOps.contain(image.convert("RGBA"), inner, Image.Resampling.LANCZOS)
    canvas.alpha_composite(thumb, ((size[0] - thumb.width) // 2,
                                 (size[1] - thumb.height) // 2))
    return canvas


def save_png(image, path, maximum=500_000):
    image.save(path, optimize=True)
    if path.stat().st_size > maximum:
        image.quantize(colors=256, method=Image.Quantize.FASTOCTREE).save(path, optimize=True)
    if path.stat().st_size > maximum:
        raise ValueError(f"Artwork exceeds byte limit: {path.name}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cover", required=True, type=Path)
    parser.add_argument("--banner", required=True, type=Path)
    parser.add_argument("--gifs", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--icon-box", type=float, nargs=4, required=True,
                        metavar=("LEFT", "TOP", "RIGHT", "BOTTOM"))
    parser.add_argument("--color", required=True, help="Background color for appreciation artwork")
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("Output already exists; choose a new version")
    l, t, r, b = args.icon_box
    if not 0 <= l < r <= 1 or not 0 <= t < b <= 1:
        raise SystemExit("Icon crop must use normalized coordinates")
    cover = Image.open(args.cover).convert("RGBA")
    if cover.getchannel("A").getextrema()[0] != 0:
        raise SystemExit("Cover source must have actual transparency")
    gifs = sorted(args.gifs.glob("*.gif"))
    if not 8 <= len(gifs) <= 24:
        raise SystemExit("Expected 8-24 existing approved GIFs")
    args.output.mkdir(parents=True)
    (args.output / "gifs").mkdir()
    save_png(fitted(cover, (240, 240), margin=8), args.output / "cover.png")
    box = tuple(round(v * (cover.width if i % 2 == 0 else cover.height))
                for i, v in enumerate(args.icon_box))
    save_png(fitted(cover.crop(box), (50, 50), margin=2), args.output / "icon.png", 100_000)
    banner = Image.open(args.banner).convert("RGB")
    ImageOps.fit(banner, (750, 400), Image.Resampling.LANCZOS).save(
        args.output / "banner.jpg", quality=92, optimize=True)
    for name, size in [("reward-guide.png", (750, 560)), ("reward-thanks.png", (750, 750))]:
        save_png(fitted(cover, size, args.color, margin=28), args.output / name)
    hashes = {}
    for source in gifs:
        dest = args.output / "gifs" / source.name
        shutil.copy2(source, dest)
        if digest(source) != digest(dest):
            raise ValueError(f"Copy mismatch: {source.name}")
        hashes[source.name] = digest(dest)
    manifest = {"operation": "format approved artwork; byte-identical GIF copies",
                "source_cover_sha256": digest(args.cover),
                "source_banner_sha256": digest(args.banner),
                "icon_box_normalized": args.icon_box, "background": args.color,
                "gif_sha256": hashes}
    (args.output / "packaging-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "preserved_gifs": len(gifs)}))


if __name__ == "__main__":
    main()
