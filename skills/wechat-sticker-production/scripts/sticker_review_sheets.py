#!/usr/bin/env python3
"""Sample sticker animation phases at native/chat size for visual inspection."""
import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageSequence


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("gifs", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    files = sorted(args.gifs.glob("*.gif"))
    for offset in range(0, len(files), 6):
        page = Image.new("RGB", (960, 6 * 210), "#f3f7f6")
        draw = ImageDraw.Draw(page)
        for row, path in enumerate(files[offset:offset + 6]):
            with Image.open(path) as gif:
                frames = [frame.convert("RGB") for frame in ImageSequence.Iterator(gif)]
            draw.text((8, row * 210 + 5), path.stem, fill="black")
            for col, fraction in enumerate((0, .25, .5, .75, .98)):
                frame = frames[round((len(frames) - 1) * fraction)]
                size = 180 if col < 4 else 120
                page.paste(frame.resize((size, size), Image.Resampling.LANCZOS),
                           (col * 190, row * 210 + 25))
        dest = args.output / f"page-{offset // 6 + 1:02}.png"
        if dest.exists():
            raise SystemExit("Preserve earlier review; choose a new output directory")
        page.save(dest)


if __name__ == "__main__":
    main()
