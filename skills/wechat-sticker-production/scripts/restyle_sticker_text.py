#!/usr/bin/env python3
"""Restyle labels in a known blank GIF caption band without changing the animation."""
import argparse
import hashlib
import html
import json
import math
from pathlib import Path
import shutil
import subprocess
import tempfile

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageSequence
from fontTools.ttLib import TTFont


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_gif(path):
    with Image.open(path) as gif:
        loop = gif.info.get("loop")
        frames, times = [], []
        for frame in ImageSequence.Iterator(gif):
            if frame.convert("RGBA").getextrema()[3] != (255, 255):
                raise ValueError("Transparent source requires a separate compositing workflow")
            frames.append(frame.convert("RGB"))
            times.append(frame.info.get("duration", 0))
    if len(frames) < 2 or any(t <= 0 for t in times) or loop != 0:
        raise ValueError("Expected a timed, infinitely looping GIF")
    return frames, times


def overlay(size, item, font_path, phase):
    """Supersampling rounds glyph outlines; the small motion never hides the words."""
    scale = 4
    font_size = item.get("font_size", 28)
    font = ImageFont.truetype(str(font_path), font_size * scale)
    label = item["label"]
    vertical = item.get("vertical", False)
    spacing = (font_size + 4) * scale
    width = (font_size + 22) * scale if vertical else (len(label) * (font_size + 2) + 22) * scale
    height = (len(label) * (font_size + 4) + 22) * scale if vertical else (font_size + 26) * scale
    tile = Image.new("RGBA", (width, height))
    draw = ImageDraw.Draw(tile)
    for i, char in enumerate(label):
        wave = math.sin(phase + i * .7) * item.get("bounce", 1.5) * scale
        x = width / 2 if vertical else (11 + font_size / 2 + i * (font_size + 2)) * scale
        y = (11 + font_size / 2) * scale + (i * spacing if vertical else 0) + wave
        draw.text((x, y), char, font=font, anchor="mm", fill="white",
                  stroke_width=4 * scale, stroke_fill="white")
        draw.text((x, y), char, font=font, anchor="mm", fill="white",
                  stroke_width=2 * scale, stroke_fill="black")
    rotation = item.get("angle", 0) + math.sin(phase) * item.get("wiggle", 1.2)
    tile = tile.rotate(rotation, Image.Resampling.BICUBIC, expand=True)
    layer = Image.new("RGBA", (size[0] * scale, size[1] * scale))
    cx, cy = item["center"]
    x, y = round(cx * scale - tile.width / 2), round(cy * scale - tile.height / 2)
    bbox = tile.getbbox()
    if bbox and (x + bbox[0] < scale or y + bbox[1] < scale or
                 x + bbox[2] > layer.width - scale or y + bbox[3] > layer.height - scale):
        raise ValueError(f"Text clips the canvas: {item['label']}")
    layer.alpha_composite(tile, (x, y))
    return layer.resize(size, Image.Resampling.LANCZOS)


def composite_exact(source, layer, erase_band, palette=None):
    base = np.array(source)
    x0, y0, x1, y1 = erase_band
    base[y0:y1, x0:x1] = base[-1, 0]
    # Use the original palette for text too; no new color-depth boundary or art quantization.
    used, indices = np.unique(base.reshape(-1, 3), axis=0, return_inverse=True)
    if palette is None:
        palette = used
    if len(palette) > 256:
        raise ValueError("Source has more than 256 colors; refusing to requantize artwork")
    lookup = {tuple(color): i for i, color in enumerate(palette)}
    remap = np.array([lookup[tuple(c)] for c in used], dtype=np.uint8)
    indexed = remap[indices].reshape(base.shape[:2])
    alpha = np.array(layer)[:, :, 3] > 0
    rgb = np.array(Image.alpha_composite(Image.fromarray(base).convert("RGBA"), layer).convert("RGB"))
    wanted, reverse = np.unique(rgb[alpha], axis=0, return_inverse=True)
    if len(wanted):
        delta = wanted.astype(np.int32)[:, None] - palette.astype(np.int32)[None]
        nearest = (delta * delta).sum(axis=2).argmin(axis=1)
        indexed[alpha] = nearest[reverse]
    result = Image.fromarray(indexed).convert("P")
    colors = palette.tolist()
    colors += [colors[-1]] * (256 - len(colors))
    result.putpalette([c for color in colors for c in color])
    allowed = alpha.copy()
    allowed[y0:y1, x0:x1] = True
    assert np.array_equal(np.array(result.convert("RGB"))[~allowed], np.array(source)[~allowed])
    return result, allowed


def verify_animation(source_frames, times, output, masks):
    result, result_times = load_gif(output)
    if times != result_times or len(result) != len(source_frames):
        raise ValueError("Frame timing changed")
    for old, new, allowed in zip(source_frames, result, masks):
        if old.size != new.size or not np.array_equal(np.array(old)[~allowed], np.array(new)[~allowed]):
            raise ValueError("Non-text pixels changed")


def restyle(source, output, item, font, erase_band, optimizer=None):
    if output.exists() or output.with_suffix(".json").exists() or output.with_suffix(".png").exists():
        raise FileExistsError(f"Use a new variant folder: {output.name}")
    frames, times = load_gif(source)
    if frames[0].size != (240, 240):
        raise ValueError("Expected 240-square source")
    if erase_band != [0, 185, 240, 240]:
        raise ValueError("This workflow only erases the verified separate bottom caption band")
    # The existing converter limits artwork to y < 180. Never mask a caption on artwork.
    for frame in frames:
        if np.min(np.array(frame)[180:190]) < 248:
            raise ValueError("Caption band is not isolated from the artwork")
    colors = {color for frame in frames for count, color in frame.getcolors(1000000)}
    palette = np.array(sorted(colors), dtype=np.uint8)
    if len(palette) > 256:
        raise ValueError("Multiple source palettes need a separate color-preserving workflow")
    elapsed = 0
    rendered, masks = [], []
    total = sum(times)
    for frame, duration in zip(frames, times):
        steps = item.get("motion_steps", 8)
        if not isinstance(steps, int) or not 4 <= steps <= 60:
            raise ValueError("motion_steps must be an integer from 4 to 60")
        phase = 2 * math.pi * round(elapsed / total * steps) / steps
        result, mask = composite_exact(frame, overlay(frame.size, item, font, phase), erase_band, palette)
        rendered.append(result)
        masks.append(mask)
        elapsed += duration
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="sticker-text-") as directory:
        candidate = Path(directory) / "text.gif"
        rendered[0].save(candidate, save_all=True, append_images=rendered[1:],
                         duration=times, loop=0, disposal=1, optimize=False)
        verify_animation(frames, times, candidate, masks)
        if optimizer:
            optimized = Path(directory) / "optimized.gif"
            subprocess.run([str(optimizer), "-O3", str(candidate), "-o", str(optimized)], check=True)
            verify_animation(frames, times, optimized, masks)
            if optimized.stat().st_size < candidate.stat().st_size:
                candidate = optimized
        shutil.copyfile(candidate, output)
    rendered[0].convert("RGB").save(output.with_suffix(".png"))
    report = {"file": output.name, "source_file": source.name, "source_sha256": digest(source),
              "gif_sha256": digest(output), "font_sha256": digest(font), "label": item["label"],
              "layout": item, "erase_band": erase_band, "frames": len(frames),
              "duration_ms": total, "frame_durations_preserved": True,
              "non_text_pixels_identical": True, "bytes": output.stat().st_size,
              "under_500000_bytes": output.stat().st_size <= 500000,
              "platform_submission": "not_submitted"}
    output.with_suffix(".json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    return report


def write_gallery(destination, reports, title):
    cards = []
    for i, report in enumerate(reports, 1):
        filename, label = html.escape(report["file"], quote=True), html.escape(report["label"])
        cards.append(f'<figure><img src="gifs/{filename}" data-file="{filename}" width="240" height="240" alt="{label}">'
                     f'<figcaption><span>{i:02d} / {label}</span><a href="gifs/{filename}" download>GIF</a></figcaption></figure>')
    page = '''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITLE__</title><style>
*{box-sizing:border-box}body{margin:0;background:#f3f7f6;color:#183d37;font:15px system-ui,sans-serif;letter-spacing:0}
header,main{max-width:1200px;margin:auto;padding:24px}header img{width:520px;max-width:100%;height:auto;display:block;border-radius:6px}
h1{font-size:24px;margin:22px 0 8px}p{color:#5a706c;margin:6px 0}nav{display:flex;gap:8px;flex-wrap:wrap;margin-top:20px}
button{font:inherit;border:1px solid #b9cbc5;padding:8px 16px;background:white;border-radius:6px;color:inherit;cursor:pointer}
button[aria-pressed=true]{background:#205f50;color:white;border-color:#205f50}main{padding-top:0;display:grid;grid-template-columns:repeat(auto-fit,minmax(256px,1fr));gap:14px}
figure{background:white;border:1px solid #dce7e2;border-radius:7px;padding:12px;margin:0;min-width:0}figure img{display:block;width:240px;height:240px;max-width:100%;object-fit:contain;margin:auto}
figcaption{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:14px 2px 3px;color:#425c55;font-size:13px}a{color:#205f50}
body.small figure img{width:240px;height:240px;transform:scale(.5)}
@media(max-width:560px){header,main{padding:16px}main{grid-template-columns:1fr}h1{font-size:21px}}
</style><header><img src="banner.jpg" alt="专辑封面"><h1>__TITLE__</h1>
<p>__COUNT__ 张 · 文字试装版 · 原动画保留 · 待选择</p><nav aria-label="版本"><button data-mode="gifs" aria-pressed="true">新版文字</button><button data-mode="originals" aria-pressed="false">原版文字</button><button id="size" aria-pressed="false">聊天尺寸</button></nav></header>
<main>__CARDS__</main><script>
document.querySelectorAll('[data-mode]').forEach(b=>b.onclick=()=>{document.querySelectorAll('[data-mode]').forEach(x=>x.setAttribute('aria-pressed',x===b));document.querySelectorAll('main figure img').forEach(i=>{i.src=b.dataset.mode+'/'+i.dataset.file;i.closest('figure').querySelector('a').href=i.src})});
document.getElementById('size').onclick=function(){this.setAttribute('aria-pressed',document.body.classList.toggle('small'))};
</script></html>'''
    (destination / "index.html").write_text(page.replace("__TITLE__", html.escape(title)).replace("__COUNT__", str(len(reports))).replace("__CARDS__", "".join(cards)), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("album", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--layout", required=True, type=Path)
    parser.add_argument("--font", required=True, type=Path)
    parser.add_argument("--gifsicle", type=Path)
    parser.add_argument("--only", type=int, help="Render just one numbered sample")
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output directory exists; choose a new version")
    config = json.loads(args.layout.read_text())
    items = config["items"]
    if args.only is not None and not 1 <= args.only <= len(items):
        parser.error("--only must identify an existing numbered sticker")
    font = TTFont(args.font)
    cmap = font.getBestCmap()
    missing = {c for item in items for c in item["label"] if ord(c) not in cmap}
    font.close()
    if missing:
        parser.error(f"Font lacks glyphs: {sorted(missing)}")
    files = sorted((args.album / "gifs").glob("*.gif"))
    if set(p.name for p in files) != set(i["file"] for i in items):
        parser.error("layout and source GIFs differ")
    args.output.mkdir(parents=True)
    reports = []
    for number, item in enumerate(items, 1):
        if args.only and number != args.only:
            continue
        source = args.album / "gifs" / item["file"]
        report = restyle(source, args.output / "gifs" / source.name, item, args.font,
                         config["erase_band"], args.gifsicle)
        (args.output / "originals").mkdir(exist_ok=True)
        shutil.copy2(source, args.output / "originals" / source.name)
        reports.append(report)
        print(json.dumps({key: report[key] for key in ("file", "bytes", "non_text_pixels_identical", "under_500000_bytes")}), flush=True)
    shutil.copy2(args.album / "banner.jpg", args.output / "banner.jpg")
    shutil.copy2(args.layout, args.output / "layout.json")
    (args.output / "audit.json").write_text(json.dumps({"count": len(reports), "reports": reports}, ensure_ascii=False, indent=2) + "\n")
    write_gallery(args.output, reports, config["title"])


if __name__ == "__main__":
    main()
