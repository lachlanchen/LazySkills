#!/usr/bin/env python3
"""Reject cross-album packaging reuse, including losslessly re-encoded copies."""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageOps

ROLES = ("cover.png", "icon.png", "banner.jpg", "reward-guide.png", "reward-thanks.png")


def visual_fingerprint(path):
    with Image.open(path) as image:
        rgba = image.convert("RGBA")
        canvas = Image.new("RGBA", rgba.size, "white")
        canvas.alpha_composite(rgba)
        rgb = canvas.convert("RGB")
        exact = hashlib.sha256(str(rgb.size).encode() + rgb.tobytes()).hexdigest()
        gray = ImageOps.grayscale(rgb).resize((9, 8), Image.Resampling.LANCZOS)
        pixels = list(gray.getdata())
        bits = [pixels[y * 9 + x] > pixels[y * 9 + x + 1] for y in range(8) for x in range(8)]
        return exact, sum(int(bit) << i for i, bit in enumerate(bits))


def check(albums):
    failures, warnings, seen = [], [], {}
    for album in albums:
        for role in ROLES:
            path = album / role
            if not path.is_file():
                failures.append(f"Missing {album.name}/{role}")
                continue
            exact, perceptual = visual_fingerprint(path)
            for other, old_exact, old_perceptual in seen.get(role, []):
                if exact == old_exact:
                    failures.append(f"Repeated {role}: {other} and {album}")
                elif (perceptual ^ old_perceptual).bit_count() <= 5:
                    warnings.append(f"Visually similar {role}: {other} and {album}; inspect manually")
            seen.setdefault(role, []).append((album, exact, perceptual))
    return {"passed": not failures, "failures": failures, "warnings": warnings,
            "note": "Hash checks supplement, not replace, visual review and platform review."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("albums", nargs="+", type=Path)
    args = parser.parse_args()
    if len({p.resolve() for p in args.albums}) != len(args.albums):
        raise SystemExit("Pass each album once")
    result = check(args.albums)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
