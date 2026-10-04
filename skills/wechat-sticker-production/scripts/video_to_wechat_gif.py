#!/usr/bin/env python3
"""Create a bounded, looping WeChat sticker from an owned video excerpt."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import tempfile

from PIL import Image, ImageFont, ImageSequence


def run(args):
    subprocess.run(args, check=True)


def sha256(path):
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--start", type=float, default=0)
    parser.add_argument("--duration", type=float, required=True)
    parser.add_argument("--speed", type=float, default=1)
    parser.add_argument("--fps", type=int, default=12)
    parser.add_argument("--dither", choices=("none", "bayer"), default="none")
    parser.add_argument("--label", default="")
    parser.add_argument("--font", type=Path)
    parser.add_argument("--max-bytes", type=int, default=500_000)
    args = parser.parse_args()
    if not args.input.is_file():
        parser.error("input must be an existing video")
    if (not all(math.isfinite(x) for x in (args.start, args.duration, args.speed))
            or args.start < 0 or args.duration <= 0 or args.speed <= 0
            or not 1 <= args.fps <= 30):
        parser.error("invalid time, speed or fps")
    if args.max_bytes <= 0 or args.output.suffix.lower() != ".gif":
        parser.error("positive max-bytes and a .gif output are required")
    preview = args.output.with_suffix(".png")
    manifest = args.output.with_suffix(".json")
    if any(path.exists() for path in (args.output, preview, manifest)):
        parser.error("output already exists; choose a new version name")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-threads", "2"]
    with tempfile.TemporaryDirectory(prefix="wechat-gif-") as temporary:
        work = Path(temporary)
        label_filter = ""
        if args.label:
            if not args.font or not args.font.is_file():
                parser.error("a valid --font is required for the label")
            font = ImageFont.truetype(str(args.font), 32)
            if "\n" in args.label or font.getlength(args.label) > 224:
                parser.error("label must fit on one line within 224 pixels")
            shutil.copyfile(args.font, work / "font.ttf")
            (work / "label.txt").write_text(args.label, encoding="utf-8")
            label_filter = (
                f",drawtext=fontfile={work}/font.ttf:textfile={work}/label.txt:"
                "expansion=none:fontsize=32:fontcolor=0x214a3b:borderw=1:"
                "bordercolor=white:x=(w-text_w)/2:y=193"
            )
        chosen = None
        attempts = []
        # Re-encode only this local derivative; source and prior versions stay intact.
        for fps, colors in [(args.fps, 256), (args.fps, 128), (args.fps, 80), (min(args.fps, 10), 64),
                            (min(args.fps, 8), 48)]:
            candidate = work / "candidate.gif"
            height = 180 if args.label else 240
            filters = (
                f"setpts=(PTS-STARTPTS)/{args.speed},fps={fps},"
                f"scale=240:{height}:force_original_aspect_ratio=decrease:flags=lanczos,"
                f"pad=240:240:(ow-iw)/2:({height}-ih)/2:color=white,setsar=1"
                + label_filter
                + f",split[a][b];[a]palettegen=max_colors={colors}:stats_mode=diff[p];"
                f"[b][p]paletteuse=dither={args.dither}:bayer_scale=3:diff_mode=rectangle"
            )
            run(ffmpeg + ["-ss", str(args.start), "-t", str(args.duration), "-i", str(args.input),
                          "-filter_complex_threads", "1", "-filter_complex", filters,
                          "-an", "-loop", "0", "-y", str(candidate)])
            size = candidate.stat().st_size
            attempts.append({"fps": fps, "colors": colors, "bytes": size})
            if size <= args.max_bytes:
                chosen = candidate
                break
        if chosen is None:
            raise SystemExit("Cannot meet the byte limit. Choose a shorter excerpt; no output accepted.")
        with Image.open(chosen) as gif:
            durations = [frame.info.get("duration", 0) for frame in ImageSequence.Iterator(gif)]
            if gif.size != (240, 240) or gif.n_frames < 2 or gif.info.get("loop") != 0:
                raise SystemExit("GIF validation failed")
            gif.seek(0)
            gif.convert("RGB").save(preview)
            details = {"width": 240, "height": 240, "frames": gif.n_frames,
                       "duration_ms": sum(durations), "loop": 0}
        shutil.copyfile(chosen, args.output)
        details.update({"source_filename": args.input.name,
                        "source_sha256": sha256(args.input),
                        "gif_sha256": sha256(args.output),
                        "start": args.start, "source_duration": args.duration,
                        "speed": args.speed, "label": args.label, "dither": args.dither,
                        "attempts": attempts,
                        "bytes": args.output.stat().st_size,
                        "platform_submission": "not_submitted"})
        manifest.write_text(json.dumps(details, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(json.dumps(details, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
