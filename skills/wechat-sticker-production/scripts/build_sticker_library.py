#!/usr/bin/env python3
"""Build a portable all-packs sticker library from explicit local album inputs."""
import argparse
import hashlib
import html
import json
from pathlib import Path
import re
import shutil

from PIL import Image
from sticker_gallery_viewer import viewer_markup


def build(config, output):
    output.mkdir(parents=True, exist_ok=True)
    (output / "gifs").mkdir(exist_ok=True)
    cards, packs, reports = [], [], []
    for pack in config["packs"]:
        if not re.fullmatch(r"[a-z0-9-]+", pack["id"]):
            raise ValueError("Pack id must be a portable slug")
        folder = Path(pack["folder"]).expanduser()
        files = sorted((folder / "gifs").glob("*.gif"))
        packs.append({"id": pack["id"], "title": pack["title"], "status": pack["status"],
                      "count": len(files), "expected": pack.get("expected", len(files))})
        for path in files:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            name = pack["id"] + "-" + path.stem + "-" + digest[:12] + ".gif"
            dest = output / "gifs" / name
            if not dest.exists():
                shutil.copy2(path, dest)
            if hashlib.sha256(dest.read_bytes()).hexdigest() != digest:
                raise ValueError("Existing copy does not match; preserve and inspect")
            sidecar = path.with_suffix(".json")
            info = json.loads(sidecar.read_text()) if sidecar.exists() else {}
            label = pack.get("labels", {}).get(path.name) or info.get("label") or info.get("layout", {}).get("label") or path.stem
            with Image.open(path) as image:
                size, frames = image.size, image.n_frames
            note = pack.get("notes", {}).get(path.name, "")
            reports.append({"file": "gifs/" + name, "pack": pack["id"], "label": label,
                            "sha256": digest, "bytes": path.stat().st_size, "frames": frames,
                            "size": size, "note": note})
            esc = html.escape
            cards.append(f'<figure data-pack="{esc(pack["id"])}" data-search="{esc(label+" "+pack["title"], quote=True)}">'
                         f'<div class="stage"><img loading="lazy" width="240" height="240" src="gifs/{name}" alt="{esc(label, quote=True)}"></div>'
                         f'<figcaption><strong>{esc(label)}</strong><span>{esc(pack["title"])}</span>'
                         f'<small>{esc(note or pack["status"])}</small><a href="gifs/{name}" download>GIF</a></figcaption></figure>')
    options = '<option value="">全部系列</option>' + "".join(f'<option value="{p["id"]}">{html.escape(p["title"])}</option>' for p in packs)
    rows = "".join(f'<tr><td><a href="#pack-{p["id"]}" data-choose-pack="{p["id"]}">{html.escape(p["title"])}</a></td><td>{p["count"]}/{p["expected"]}</td><td>{html.escape(p["status"])}</td></tr>' for p in packs)
    page = '''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>四位伙伴 · 表情收藏室</title><style>
*{box-sizing:border-box}body{margin:0;background:#f3f7f6;color:#183d37;font:15px system-ui,sans-serif;letter-spacing:0}
header,main,footer{max-width:1280px;margin:auto;padding:24px}h1{font-size:27px;margin:0 0 8px}.names{color:#69796f;margin:0 0 20px}
table{border-collapse:collapse;width:100%;max-width:820px;font-size:14px;margin-bottom:20px}td,th{text-align:left;padding:8px 10px;border-bottom:1px solid #dce5df}th{font-weight:600}nav{display:flex;gap:10px;flex-wrap:wrap;align-items:center}
select,input,button{font:inherit;color:inherit;border:1px solid #bbcfc4;border-radius:6px;background:white;padding:9px 12px;max-width:100%}input{width:240px}button{cursor:pointer}button[aria-pressed=true]{background:#205f50;color:white}
main{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:14px;padding-top:0}figure{margin:0;min-width:0;border:1px solid #dae6df;background:white;border-radius:7px;padding:12px}figure[hidden]{display:none}
.stage{height:240px;display:flex;align-items:center;justify-content:center}img{width:240px;height:240px;max-width:100%;object-fit:contain}.small img{width:120px;height:120px}
figcaption{display:grid;grid-template-columns:1fr auto;gap:6px;font-size:13px;padding-top:10px}strong{font-size:15px}figcaption span,small{grid-column:1;color:#6b7c73}figcaption a{grid-column:2;grid-row:1;color:#205f50}footer{color:#718277;font-size:13px}
@media(max-width:600px){header,main,footer{padding:14px}main{grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}figure{padding:8px}.stage{height:auto;aspect-ratio:1}.stage img{height:auto;aspect-ratio:1}.small .stage img{width:96px}h1{font-size:23px}td,th{padding:8px 4px}}
</style><header><h1>四位伙伴 · 表情收藏室</h1><p class="names">啦啦侠 · 阿芽酱 · 飒飒君 · 庄子机器人</p>
<table><thead><tr><th>系列</th><th>已有 / 计划</th><th>状态</th></tr></thead><tbody>__ROWS__</tbody></table>
<nav><select id="pack" aria-label="系列">__OPTIONS__</select><input id="query" type="search" placeholder="查找表情" aria-label="查找表情"><button id="size" aria-pressed="false">120 px</button><span id="count"></span></nav></header>
<main>__CARDS__</main><footer>原版保留 · 新系列草稿供检查 · 后续正式上传使用贴边版</footer><script>
const figures=[...document.querySelectorAll('figure')],p=document.getElementById('pack'),q=document.getElementById('query');function filter(){let n=0;figures.forEach(f=>{f.hidden=!!((p.value&&f.dataset.pack!==p.value)||!f.dataset.search.toLowerCase().includes(q.value.toLowerCase()));if(!f.hidden)n++});document.getElementById('count').textContent=n+' 张'}p.onchange=filter;q.oninput=filter;document.getElementById('size').onclick=function(){this.setAttribute('aria-pressed',String(document.body.classList.toggle('small')))};filter();
</script><script>document.querySelectorAll('[data-choose-pack]').forEach(a=>a.onclick=e=>{e.preventDefault();document.getElementById('pack').value=a.dataset.choosePack;document.getElementById('query').value='';filter();document.querySelector('nav').scrollIntoView({block:'start'});});</script>__VIEWER__</html>'''
    (output / "index.html").write_text(page.replace("__ROWS__", rows).replace("__OPTIONS__", options).replace("__CARDS__", "".join(cards)).replace("__VIEWER__", viewer_markup()), encoding="utf-8")
    audit = {"packs": packs, "gif_count": len(reports), "files": reports}
    (output / "audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"packs": packs, "gif_count": len(reports)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    print(json.dumps(build(json.loads(args.config.read_text()), args.output), ensure_ascii=False))


if __name__ == "__main__":
    main()
