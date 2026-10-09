#!/usr/bin/env python3
"""Build a portable, read-only original/compact/edge sticker comparison gallery."""
import argparse
import hashlib
import html
import json
from pathlib import Path
import shutil

from PIL import Image, ImageSequence


def inspect(path):
    with Image.open(path) as image:
        times = [frame.info.get("duration", 0) for frame in ImageSequence.Iterator(image)]
        if image.size != (240, 240) or len(times) < 2 or image.info.get("loop") != 0:
            raise ValueError(f"Not a looping 240-square GIF: {path.name}")
        if path.stat().st_size > 500_000 or min(times) <= 0:
            raise ValueError(f"GIF exceeds size or has invalid delays: {path.name}")
    return {"bytes": path.stat().st_size, "frames": len(times), "duration_ms": sum(times),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def build(config, output):
    labels = [("original", "原留白"), ("compact", "紧凑版"), ("edge", "贴边版")]
    if not config.get("items") or output.exists():
        raise ValueError("Provide items and a new output directory")
    pending = []
    for index, item in enumerate(config["items"], 1):
        for key, label in labels:
            source = Path(item[key]).expanduser().resolve()
            pending.append((index, item["label"], key, label, source, inspect(source)))
    (output / "gifs").mkdir(parents=True)
    reports, sections = [], []
    for index, item in enumerate(config["items"], 1):
        cards = []
        for number, title, key, label, source, report in pending:
            if number != index:
                continue
            name = f"{index:02d}-{key}.gif"
            dest = output / "gifs" / name
            shutil.copy2(source, dest)
            if hashlib.sha256(dest.read_bytes()).hexdigest() != report["sha256"]:
                raise ValueError("Copy hash mismatch")
            reports.append({"file": "gifs/" + name, "label": title, "variant": key, **report})
            fps = report["frames"] / (report["duration_ms"] / 1000)
            cards.append(f'<figure><h3>{label}</h3><div class="stage"><img src="gifs/{name}" '
                         f'width="240" height="240" alt="{html.escape(title, quote=True)} · {label}"></div>'
                         f'<figcaption><span>{report["bytes"]/1000:.0f} KB · {fps:.0f} fps</span>'
                         f'<a href="gifs/{name}" download>GIF</a></figcaption></figure>')
        sections.append(f'<section><h2>{index:02d} / {html.escape(item["label"])}</h2>'
                        f'<div class="grid">{"".join(cards)}</div></section>')
    page = '''<!doctype html>
<html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITLE__</title><style>
*{box-sizing:border-box}body{margin:0;background:#f3f7f6;color:#183d37;font:15px system-ui,sans-serif;letter-spacing:0}
header,main,footer{max-width:1020px;margin:auto;padding:24px}header{padding-bottom:12px}h1{font-size:26px;margin:0 0 8px}
.status{color:#647570;margin:0}nav{display:flex;gap:6px;flex-wrap:wrap;margin-top:18px}button{font:inherit;border:1px solid #b9cbc5;padding:8px 14px;background:#fff;border-radius:6px;color:inherit;cursor:pointer}
button[aria-pressed=true]{background:#205f50;color:#fff;border-color:#205f50}button:focus-visible,a:focus-visible{outline:3px solid #b98534;outline-offset:3px}
main{padding-top:0}section{margin:0 0 28px}h2{font-size:18px;margin:14px 0}h3{font-size:14px;margin:0 0 10px;font-weight:600}
.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}figure{min-width:0;margin:0;padding:14px;background:#fff;border:1px solid #dce7e2;border-radius:7px}
.stage{height:240px;display:flex;align-items:center;justify-content:center}figure img{display:block;width:240px;height:240px;max-width:100%;object-fit:contain}
body.small figure img{width:120px;height:120px}figcaption{display:flex;align-items:center;justify-content:space-between;font-size:13px;color:#60716b;margin-top:10px;gap:8px}a{color:#205f50}footer{padding-top:0;font-size:13px;color:#60716b}
@media(max-width:860px){.grid{grid-template-columns:1fr}header,main,footer{padding:18px}main{padding-top:0}h1{font-size:23px}}
</style><header><h1>__TITLE__</h1><p class="status">阿芽酱 · 啦啦侠 · 庄子 / 待选择</p>
<nav aria-label="预览尺寸"><button data-size="full" aria-pressed="true">240 px</button><button data-size="small" aria-pressed="false">120 px</button><button id="restart">重新播放</button></nav></header>
<main>__SECTIONS__</main><footer>原文件保留 · 新版未上传 · 仅后期裁剪与排字</footer>
<script>
document.querySelectorAll('[data-size]').forEach(b=>b.onclick=()=>{document.body.classList.toggle('small',b.dataset.size==='small');document.querySelectorAll('[data-size]').forEach(x=>x.setAttribute('aria-pressed',String(x===b)))});
document.getElementById('restart').onclick=()=>{const stamp=Date.now();document.querySelectorAll('main img').forEach(i=>{i.src=i.getAttribute('src').split('?')[0]+'?r='+stamp})};
</script></html>'''
    (output / "index.html").write_text(page.replace("__TITLE__", html.escape(config.get("title", "表情留白试装")))
                                      .replace("__SECTIONS__", "".join(sections)), encoding="utf-8")
    audit = {"gif_count": len(reports), "platform_submission": "not_submitted", "reports": reports}
    (output / "audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return audit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path, help="JSON: items with label, original, compact and edge paths")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    print(json.dumps(build(json.loads(args.config.read_text(encoding="utf-8")), args.output), indent=2))


if __name__ == "__main__":
    main()
