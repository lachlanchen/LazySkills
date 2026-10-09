#!/usr/bin/env python3
"""Audit an explicit WeChat GIF album and write a portable offline gallery."""
import argparse
import hashlib
import html
import json
from pathlib import Path

from PIL import Image, ImageChops, ImageStat
from sticker_gallery_viewer import viewer_markup


def require(condition, message):
    if not condition:
        raise ValueError(message)


def audit(path):
    with Image.open(path) as image:
        require(image.size == (240, 240), f"{path.name}: wrong dimensions")
        require(image.format == "GIF" and image.n_frames > 1, f"{path.name}: not animated")
        require(image.info.get("loop") == 0, f"{path.name}: not infinite loop")
        require(path.stat().st_size <= 500_000, f"{path.name}: over 500000 bytes")
        frames = []
        milliseconds = 0
        for index in range(image.n_frames):
            image.seek(index)
            milliseconds += image.info.get("duration", 0)
            frames.append(image.convert("RGB"))
        difference = ImageStat.Stat(ImageChops.difference(frames[0], frames[-1]))
        unique_frames = len({hashlib.sha256(frame.tobytes()).digest() for frame in frames})
        require(unique_frames >= 2 and milliseconds > 0, f"{path.name}: frozen or zero duration")
        return {"file": path.name, "bytes": path.stat().st_size, "frames": len(frames),
                "unique_frames": unique_frames, "duration_ms": milliseconds,
                "loop_seam_mean_absolute_difference": round(sum(difference.mean) / 3, 3),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "visual_review": "required_separately"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    parser.add_argument("--expected", type=int, choices=range(8, 25), default=24)
    parser.add_argument("--partial", action="store_true")
    parser.add_argument("--title", default="啦啦侠阿芽酱 · 日常第一弹")
    parser.add_argument("--library-href", help="Optional portable link to the all-series index")
    parser.add_argument("--labels-file", type=Path, help="Optional selection JSON with id/label items")
    args = parser.parse_args()
    paths = sorted((args.folder / "gifs").glob("*.gif"))
    if not args.partial and len(paths) != args.expected:
        raise SystemExit(f"Expected {args.expected} GIFs, found {len(paths)}")
    results = [audit(path) for path in paths]
    require(len({item["sha256"] for item in results}) == len(results), "Duplicate GIF content")
    for name, size, maximum, alpha in [("cover.png", (240, 240), 500000, True),
                                      ("icon.png", (50, 50), 100000, True),
                                      ("banner.jpg", (750, 400), 500000, False)]:
        path = args.folder / name
        with Image.open(path) as image:
            require(image.size == size and path.stat().st_size <= maximum, f"Bad {name}")
            if alpha:
                require("A" in image.getbands() and image.getchannel("A").getextrema()[0] == 0, f"No transparency: {name}")
    (args.folder / "audit.json").write_text(json.dumps({"expected": args.expected, "count": len(paths),
        "complete": len(paths) == args.expected, "files": results}, indent=2, ensure_ascii=False) + "\n")
    figures = []
    labels = {}
    if args.labels_file:
        labels = {item['id']: item['label'] for item in json.loads(args.labels_file.read_text())['items']}
    for path in paths:
        relative = "gifs/" + path.name
        label = labels.get(path.stem, path.stem)
        figures.append(f'<figure><a href="{html.escape(relative)}"><img width="240" height="240" src="{html.escape(relative)}" alt="{html.escape(label)}"></a><figcaption>{html.escape(label)}</figcaption></figure>')
    gallery = '''<!doctype html><html lang="zh-CN"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>啦啦侠阿芽酱 · 日常第一弹</title>
<style>*{box-sizing:border-box}body{font-family:system-ui,sans-serif;background:#f5f7f6;color:#223c33;margin:0;padding:24px;letter-spacing:0}header{max-width:1100px;margin:0 auto 24px}h1{font-size:24px;margin:12px 0}header img{max-width:750px;width:100%;height:auto}main{max-width:1100px;margin:auto;display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:16px}figure{margin:0;background:white;border:1px solid #dae3dd;border-radius:8px;text-align:center;padding:8px}figure img{width:240px;height:240px;max-width:100%;object-fit:contain}figcaption{font-size:12px;overflow-wrap:anywhere;padding:8px;color:#53655d}@media(max-width:560px){body{padding:12px}main{grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}figure img{width:100%;height:auto;aspect-ratio:1}h1{font-size:20px}}</style>
<header><img src="banner.jpg" width="750" height="400" alt="啦啦侠、阿芽酱、飒飒君和庄子"><h1>啦啦侠阿芽酱 · 日常第一弹</h1><p>COUNT</p></header><main>FIGURES</main></html>'''
    gallery = gallery.replace("COUNT", f"{len(paths)} / {args.expected}").replace("FIGURES", "".join(figures))
    gallery = gallery.replace("啦啦侠阿芽酱 · 日常第一弹", html.escape(args.title))
    if args.library_href:
        require(not args.library_href.lower().startswith(('javascript:', 'data:')), 'Unsafe gallery link')
        gallery = gallery.replace('<header>', '<header><a href="' + html.escape(args.library_href, quote=True) + '">全部表情</a>')
    gallery = gallery.replace('</html>', viewer_markup() + '</html>')
    (args.folder / "index.html").write_text(gallery, encoding="utf-8")
    print(json.dumps({"count": len(paths), "complete": len(paths) == args.expected,
                      "largest_bytes": max((x["bytes"] for x in results), default=0)}, indent=2))


if __name__ == "__main__":
    main()
