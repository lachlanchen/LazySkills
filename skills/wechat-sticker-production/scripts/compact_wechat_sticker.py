#!/usr/bin/env python3
"""Reframe an existing white-background animation with compact cute lettering."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import tempfile

import numpy as np
from fontTools.ttLib import TTFont
from PIL import Image, ImageOps, ImageSequence

from restyle_sticker_text import overlay


def decoded_timeline(path):
    """Compare displayed pixels and delays even if an optimizer coalesces frames."""
    timeline = []
    with Image.open(path) as image:
        loop = image.info.get("loop")
        for frame in ImageSequence.Iterator(image):
            digest = hashlib.sha256(frame.convert("RGBA").tobytes()).hexdigest()
            delay = frame.info.get("duration", 0)
            if timeline and timeline[-1][0] == digest:
                timeline[-1][1] += delay
            else:
                timeline.append([digest, delay])
        return image.size, loop, timeline


def encoding_options(fps):
    return list(dict.fromkeys([(fps, colors) for colors in (256, 128, 96, 80, 64)] +
                             [(min(fps, 12), 80), (min(fps, 10), 64)]))


def motion_bbox(frames, threshold=38):
    """One union crop for all frames avoids pumping and clipped moving limbs."""
    mask = np.zeros((frames[0].height, frames[0].width), dtype=bool)
    for frame in frames:
        rgb = np.asarray(frame.convert("RGB"), dtype=np.int16)
        mask |= np.max(255 - rgb, axis=2) > threshold
    rows = np.flatnonzero(mask.sum(axis=1) > 2)
    cols = np.flatnonzero(mask.sum(axis=0) > 2)
    if not len(rows) or not len(cols):
        raise ValueError("No visible foreground")
    return (max(0, int(cols[0]) - 3), max(0, int(rows[0]) - 3),
            min(frames[0].width, int(cols[-1]) + 4),
            min(frames[0].height, int(rows[-1]) + 4))


def reframe(frame, box, padding):
    scaled = ImageOps.contain(frame.crop(box).convert("RGB"),
                              (240 - 2 * padding, 240 - 2 * padding), Image.Resampling.LANCZOS)
    result = Image.new("RGB", (240, 240), "white")
    result.paste(scaled, ((240 - scaled.width) // 2, (240 - scaled.height) // 2))
    return result


def caption_layout(frames, label, font, size, center=None, vertical=False):
    occupied = np.zeros((240, 240), dtype=bool)
    for frame in frames:
        occupied |= np.max(255 - np.asarray(frame, dtype=np.int16), axis=2) > 55
    candidates = []
    placements = [(center, vertical)] if center else [
        ((48, 28), False), ((192, 28), False), ((120, 22), False),
        ((48, 213), False), ((192, 213), False), ((120, 215), False),
        ((20, 100), True), ((220, 100), True)]
    for position, is_vertical in placements:
        item = {"label": label, "center": position, "font_size": size,
                "vertical": is_vertical, "angle": -3, "bounce": .6, "wiggle": .4}
        union = np.zeros((240, 240), dtype=bool)
        try:
            for phase in np.linspace(0, 2 * math.pi, 8, endpoint=False):
                union |= np.asarray(overlay((240, 240), item, font, phase))[:, :, 3] > 16
        except ValueError:
            continue
        overlap = float(np.sum(union & occupied) / max(1, union.sum()))
        candidates.append((overlap, item))
    if not candidates:
        raise ValueError("No unclipped caption placement; reduce font size or give a center")
    overlap, item = min(candidates, key=lambda pair: pair[0])
    return item, overlap


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--label", required=True)
    parser.add_argument("--font", required=True, type=Path)
    parser.add_argument("--padding", type=int, default=6)
    parser.add_argument("--font-size", type=int, default=24)
    parser.add_argument("--center", type=float, nargs=2)
    parser.add_argument("--vertical", action="store_true")
    parser.add_argument("--duration", type=float, default=5.125)
    parser.add_argument("--speed", type=float, default=1.25)
    parser.add_argument("--fps", type=int, default=15)
    parser.add_argument("--gifsicle", type=Path, help="Optional lossless GIF optimizer")
    parser.add_argument("--max-text-overlap", type=float, default=.02,
                        help="Maximum text-mask overlap with detected foreground (default .02)")
    args = parser.parse_args()
    if not args.input.is_file() or not args.font.is_file():
        parser.error("Input and font must exist")
    if args.gifsicle and not args.gifsicle.is_file():
        parser.error("Gifsicle executable must exist")
    if not 0 <= args.padding <= 30 or not 12 <= args.font_size <= 36:
        parser.error("Invalid padding or font size")
    if not args.label.strip() or not 0 <= args.max_text_overlap <= 1:
        parser.error("Label must be nonempty and overlap must be between 0 and 1")
    if args.center and not all(math.isfinite(x) for x in args.center):
        parser.error("Caption center must be finite")
    if not all(math.isfinite(x) and x > 0 for x in (args.duration, args.speed)) or not 1 <= args.fps <= 30:
        parser.error("Invalid duration/speed/fps")
    targets = [args.output, args.output.with_suffix(".png"), args.output.with_suffix(".json")]
    if args.output.suffix.lower() != ".gif" or any(p.exists() for p in targets):
        parser.error("Choose a new .gif output path")
    with TTFont(args.font) as font:
        missing = {char for char in args.label if ord(char) not in font.getBestCmap()}
    if missing:
        parser.error(f"Missing font glyphs: {sorted(missing)}")
    ffmpeg = ["ffmpeg", "-v", "error", "-nostdin", "-threads", "2"]
    with tempfile.TemporaryDirectory(prefix="sticker-compact-") as temporary:
        root = Path(temporary)
        source = root / "source"
        source.mkdir()
        subprocess.run(ffmpeg + ["-t", str(args.duration), "-i", str(args.input), "-vf",
                                f"setpts=(PTS-STARTPTS)/{args.speed},fps={args.fps}",
                                "-threads", "2", str(source / "%04d.png")], check=True)
        frames = []
        for path in sorted(source.glob("*.png")):
            with Image.open(path) as image:
                frames.append(image.convert("RGB"))
        if len(frames) < 2:
            raise ValueError("Need an animation")
        box = motion_bbox(frames)
        reframed = [reframe(frame, box, args.padding) for frame in frames]
        item, overlap = caption_layout(reframed, args.label, args.font, args.font_size,
                                       args.center, args.vertical)
        if overlap > args.max_text_overlap:
            raise ValueError(f"Text overlaps foreground by {overlap:.1%}; revise size/position/padding")
        rendered = root / "rendered"
        rendered.mkdir()
        for index, frame in enumerate(reframed):
            phase = 2 * math.pi * round(index / len(frames) * 8) / 8
            Image.alpha_composite(frame.convert("RGBA"), overlay(frame.size, item, args.font, phase)).convert(
                "RGB").save(rendered / f"{index:04d}.png")
        attempts = []
        candidate = root / "candidate.gif"
        for fps, colors in encoding_options(args.fps):
            filters = (f"fps={fps},split[a][b];[a]palettegen=max_colors={colors}:stats_mode=diff[p];"
                       "[b][p]paletteuse=dither=none:diff_mode=rectangle")
            subprocess.run(ffmpeg + ["-framerate", str(args.fps), "-i", str(rendered / "%04d.png"),
                                    "-filter_complex_threads", "1", "-filter_complex", filters,
                                    "-loop", "0", "-y", str(candidate)], check=True)
            raw_bytes = candidate.stat().st_size
            lossless_optimized = False
            if args.gifsicle:
                optimized = root / "optimized.gif"
                subprocess.run([str(args.gifsicle.resolve()), "-O3", str(candidate),
                                "-o", str(optimized)], check=True)
                if optimized.stat().st_size < raw_bytes:
                    if decoded_timeline(candidate) != decoded_timeline(optimized):
                        raise ValueError("Optimizer changed displayed frames or timing")
                    shutil.copy2(optimized, candidate)
                    lossless_optimized = True
            attempts.append({"fps": fps, "colors": colors, "raw_bytes": raw_bytes,
                             "lossless_optimized": lossless_optimized,
                             "bytes": candidate.stat().st_size})
            if candidate.stat().st_size <= 500_000:
                break
        else:
            raise ValueError("No variant meets byte limit; keep source and revise local export")
        with Image.open(candidate) as gif:
            times = [f.info.get("duration", 0) for f in ImageSequence.Iterator(gif)]
            if gif.size != (240, 240) or gif.n_frames < 2 or gif.info.get("loop") != 0:
                raise ValueError("Invalid GIF")
            args.output.parent.mkdir(parents=True, exist_ok=True)
            gif.seek(0)
            gif.convert("RGB").save(args.output.with_suffix(".png"))
        shutil.copy2(candidate, args.output)
    report = {"operation": "existing video crop/scale and caption only; no model generation",
              "source_filename": args.input.name,
              "source_sha256": hashlib.sha256(args.input.read_bytes()).hexdigest(),
              "font_sha256": hashlib.sha256(args.font.read_bytes()).hexdigest(),
              "gif_sha256": hashlib.sha256(args.output.read_bytes()).hexdigest(),
              "crop_union": box, "padding": args.padding, "layout": item,
              "source_duration_limit": args.duration, "speed": args.speed,
              "selected_fps": fps, "selected_colors": colors,
              "caption_foreground_overlap_fraction": round(overlap, 4),
              "max_text_overlap": args.max_text_overlap,
              "needs_visual_review": True, "duration_ms": sum(times),
              "attempts": attempts, "bytes": args.output.stat().st_size,
              "platform_submission": "not_submitted"}
    args.output.with_suffix(".json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
