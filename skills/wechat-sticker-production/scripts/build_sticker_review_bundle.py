#!/usr/bin/env python3
"""Build a portable, explicitly staged sticker review without publishing it."""
import argparse
import hashlib
import html
import json
from pathlib import Path
import re
import shutil
from urllib.parse import urlsplit
import zipfile

from sticker_gallery_viewer import viewer_markup


def copy_checked(source, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        if source.read_bytes() != target.read_bytes():
            raise ValueError('Existing review asset differs: ' + target.name)
    else:
        shutil.copy2(source, target)
    return hashlib.sha256(target.read_bytes()).hexdigest()


def build(plan, source_root, destination, title, kind, back=None):
    if kind not in {'food', 'extension'}:
        raise ValueError('Unknown review kind')
    if back:
        parsed = urlsplit(back)
        if parsed.scheme not in {'', 'https', 'http'} or '\\' in back or back.startswith('//'):
            raise ValueError('Back link must be a relative page or HTTP(S) URL')
    destination.mkdir(parents=True, exist_ok=True)
    data = json.loads(plan.read_text())
    rows, assets = [], []
    seen = set()
    for item in data['items']:
        for key in ('id', 'pack') if kind == 'food' else ('id',):
            if not re.fullmatch(r'[a-z0-9][a-z0-9-]*', item[key]):
                raise ValueError('Invalid artwork slug')
        if item['id'] in seen:
            raise ValueError('Duplicate sticker id')
        seen.add(item['id'])
        if kind == 'food':
            base = source_root / item['pack']
            reference = base / 'references' / (item['id'] + '-v1.png')
            edition = item.get('gif_edition', 'edge-zh-v1')
            if not re.fullmatch(r'[a-z0-9][a-z0-9-]*', edition):
                raise ValueError('Invalid GIF edition')
            gif = base / edition / (item['id'] + '.gif')
            selection_gif = base / edition / 'gifs' / (item['id'] + '.gif')
            if selection_gif.exists():
                if gif.exists() and gif.read_bytes() != selection_gif.read_bytes():
                    raise ValueError('Conflicting selected GIF editions: ' + item['id'])
                gif = selection_gif
            label = item['zh']
        else:
            gif = source_root / 'gifs' / (item['id'] + '.gif')
            reference = gif.with_suffix('.png')
            label = item['label']
        selected = gif if gif.exists() else reference
        if not selected.is_file():
            raise FileNotFoundError(selected)
        if not selected.resolve().is_relative_to(source_root.resolve()):
            raise ValueError('Artwork is outside the selected source root')
        relative = Path('gifs' if gif.exists() else 'references') / selected.name
        digest = copy_checked(selected, destination / relative)
        row = {'id': item['id'], 'label': label, 'file': relative.as_posix(),
               'state': 'animation' if gif.exists() else 'reference_animation_pending',
               'sha256': digest}
        rows.append(row)
        assets.append(destination / relative)
    ready = sum(r['state'] == 'animation' for r in rows)
    for name in ('cover.png', 'icon.png', 'banner.jpg', 'reward-guide.png', 'reward-thanks.png'):
        if (source_root / name).is_file():
            copy_checked(source_root / name, destination / name)
    esc = lambda value: html.escape(str(value), quote=True)
    cards = ''.join('<figure><a href="' + esc(r['file']) + '"><img width="240" height="240" src="'
                    + esc(r['file']) + '" alt="' + esc(r['label']) + '"></a><figcaption><strong>'
                    + esc(r['label']) + '</strong><span>'
                    + ('GIF' if r['state'] == 'animation' else 'Reference · animation pending')
                    + '</span></figcaption></figure>' for r in rows)
    link = '<a href="' + esc(back) + '">All collections</a>' if back else ''
    zip_name = 'review-artwork.zip'
    with zipfile.ZipFile(destination / zip_name, 'w', zipfile.ZIP_DEFLATED) as bundle:
        for asset in assets:
            bundle.write(asset, asset.relative_to(destination))
    status = 'Review only · not submitted' if kind == 'food' else 'Free extension edition · not submitted'
    page = '''<!doctype html><html lang="zh-CN"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>TITLE</title>
<style>*{box-sizing:border-box}body{margin:0;color:#173644;background:#f3fbff;font:15px system-ui,sans-serif;letter-spacing:0}
header{padding:20px 24px;border-bottom:3px solid #20bfb5;background:#d7f7f4}header>div{max-width:1280px;margin:auto}
h1{font-size:26px;margin:12px 0 8px}p{margin:6px 0;line-height:1.6}a{color:#076a84;text-underline-offset:3px}
.layout{max-width:1328px;margin:auto;display:grid;grid-template-columns:174px minmax(0,1fr);gap:20px;padding:20px 24px}
aside{align-self:start;position:sticky;top:16px}aside a{display:block;padding:12px 0}aside strong{display:block;color:#b53370;font-size:14px;margin-bottom:6px}
main{min-width:0;display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}figure{margin:0;background:white;border:1px solid #cde5ed;border-radius:8px;overflow:hidden}
figure>a{display:block}figure img{display:block;width:100%;height:auto;aspect-ratio:1;object-fit:contain}
figcaption{padding:10px;border-top:1px solid #e5f0f4;display:grid;gap:4px;overflow-wrap:anywhere}figcaption strong{font-size:17px}figcaption span{font-size:11px;color:#566d79}
.note{font-size:13px;color:#506672}.pill{font-size:12px;color:#137668}button{font:inherit}
@media(max-width:1000px){main{grid-template-columns:repeat(3,minmax(0,1fr))}.layout{grid-template-columns:145px minmax(0,1fr)}}
@media(max-width:680px){header{padding:16px}.layout{display:block;padding:12px}aside{position:static;display:flex;gap:16px;align-items:center;flex-wrap:wrap;margin-bottom:12px}aside a{padding:6px 0}aside p{margin:0}aside strong{margin:0}main{grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}h1{font-size:23px}figcaption{padding:8px}}
</style><header><div>BACK<h1>TITLE</h1><p>STATUS</p><p class="pill">READY animated / TOTAL total</p></div></header>
<div class="layout"><aside><strong>AYA · LALA</strong><p class="note">Sasa &amp; Zhuangzi</p><a href="review-artwork.zip" download>Download preview</a>BACK</aside><main>CARDS</main></div></html>'''
    for key, value in {'TITLE': esc(title), 'BACK': link, 'STATUS': esc(status),
                       'READY': str(ready), 'TOTAL': str(len(rows)), 'CARDS': cards}.items():
        page = page.replace(key, value)
    viewer = viewer_markup().replace('>GIF</a>', '>Download artwork</a>')
    page = page.replace('</html>', viewer + '</html>')
    (destination / 'index.html').write_text(page)
    manifest = {'title': title, 'state': status, 'animated': ready, 'count': len(rows),
                'platform_submission': False, 'items': rows}
    (destination / 'review-manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    return {'animated': ready, 'count': len(rows), 'page': str(destination / 'index.html')}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('plan', type=Path)
    parser.add_argument('source_root', type=Path)
    parser.add_argument('destination', type=Path)
    parser.add_argument('--title', required=True)
    parser.add_argument('--kind', choices=['food', 'extension'], required=True)
    parser.add_argument('--back')
    args = parser.parse_args()
    args.destination.mkdir(parents=True, exist_ok=True)
    print(json.dumps(build(args.plan, args.source_root, args.destination, args.title, args.kind, args.back)))
