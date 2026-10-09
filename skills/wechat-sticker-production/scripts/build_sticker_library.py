#!/usr/bin/env python3
"""Build a portable sticker gallery with current editions and preserved variants."""
import argparse
import hashlib
import html
import json
from pathlib import Path
import re
import shutil

from PIL import Image
from sticker_gallery_viewer import viewer_markup
from sticker_icons import icon, LICENSE


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def preserved_editions(packs, root, output):
    """Index distinct GIF exports, not account receipts or duplicate gallery copies."""
    seen = {digest(p) for pack in packs for p in Path(pack['folder']).expanduser().joinpath('gifs').glob('*.gif')}
    grouped = {}
    for path in sorted(root.rglob('*.gif')):
        if output.resolve() in path.resolve().parents:
            continue
        relative = path.relative_to(root)
        if any(part in {'captures', 'review-sheets', 'All-Stickers', 'export-logs'} for part in relative.parts):
            continue
        sha = digest(path)
        if sha in seen:
            continue
        seen.add(sha)
        group = '/'.join(relative.parts[:2]) if 'gifs' in relative.parts else relative.parts[0] + '/native'
        grouped.setdefault(group, []).append(path)
    names = {'daily-v1': '第一弹', 'daily-v2': '第二弹', 'daily-v3': '第三弹', 'daily-v4': '第四弹',
             'daily-v5': '闪光的日常', 'daily-unique-v1': '闪光的日常 · 独立动画',
             'japanese-v1': '日文 / 空耳篇', 'phonetic-unique-v1': '空耳小日常',
             'cantonese-v1': '粤语篇', 'cantonese-unique-v1': '粤语篇 · 独立动画',
             'sports-v1': '运动篇', 'sports-unique-v1': '运动篇 · 独立动画',
             'research-v1': '科研篇', 'research-unique-v1': '科研篇 · 独立动画',
             'outing-v1': '小车篇', 'outing-unique-v1': '小车篇 · 独立动画'}
    def title(group):
        family, edition = group.split('/', 1)
        edition = edition.replace('native', '动画原版').replace('review-album', '初版预览').replace('album', '初版').replace('edge', '贴边').replace('text-cute', '可爱字').replace('text-style', '字体').replace('phonetic', '谐音')
        return names.get(family, family) + ' · ' + edition
    return [{'id': 'archive-' + hashlib.sha256(group.encode()).hexdigest()[:12],
             'title': title(group), 'status': '历史版本 · 保留对比',
             'folder': str(root), 'files': paths, 'group': 'archive'} for group, paths in grouped.items()]


def build(config, output, archive_root=None, public_only=False):
    if public_only and output.exists() and any(output.iterdir()):
        raise ValueError('Public export needs an empty destination')
    output.mkdir(parents=True, exist_ok=True)
    (output / 'gifs').mkdir(exist_ok=True)
    cards, packs, reports = [], [], []
    inputs = [dict(p) for p in config['packs']]
    for pack in inputs:
        pack.setdefault('group', 'alternatives' if pack['id'] in {'alternatives', 'deviation-candidates'} else 'archive' if pack['id'] == 'japanese' else 'current')
        if pack['group'] not in {'current', 'archive', 'alternatives'}:
            raise ValueError('Unknown edition group')
    if public_only:
        inputs = [p for p in inputs if p.get('public') is True and p['group'] == 'current']
        if not inputs:
            raise ValueError('No explicitly approved public packs; nothing exported')
    elif archive_root:
        inputs += preserved_editions(inputs, archive_root, output)
    for pack in inputs:
        if not re.fullmatch(r'[a-z0-9-]+', pack['id']):
            raise ValueError('Pack id must be a portable slug')
        folder = Path(pack['folder']).expanduser()
        files = pack.get('files', sorted((folder / 'gifs').glob('*.gif')))
        status = pack.get('public_status', '') if public_only else pack['status']
        entry = {'id': pack['id'], 'title': pack['title'], 'status': status,
                 'group': pack['group'], 'count': len(files), 'expected': pack.get('expected', len(files))}
        packs.append(entry)
        for path in files:
            sha = digest(path)
            stem = re.sub(r'[^a-zA-Z0-9_-]+', '-', path.stem).strip('-') or 'sticker'
            name = pack['id'] + '-' + stem + '-' + sha[:12] + '.gif'
            dest = output / 'gifs' / name
            if not dest.exists():
                shutil.copy2(path, dest)
            if digest(dest) != sha:
                raise ValueError('Existing copy does not match; preserve and inspect')
            sidecar = path.with_suffix('.json')
            info = json.loads(sidecar.read_text()) if sidecar.exists() else {}
            label = pack.get('labels', {}).get(path.name) or info.get('label') or info.get('layout', {}).get('label') or path.stem
            with Image.open(path) as im:
                size, frames = im.size, im.n_frames
            note = '' if public_only else pack.get('notes', {}).get(path.name, '')
            reports.append({'file': 'gifs/' + name, 'pack': pack['id'], 'group': pack['group'], 'label': label,
                            'sha256': sha, 'bytes': path.stat().st_size, 'frames': frames, 'size': size, 'note': note})
            entry.setdefault('preview', 'gifs/' + name)
            esc = html.escape
            cards.append(f'<figure data-pack="{esc(pack["id"])}" data-group="{pack["group"]}" data-search="{esc(label+" "+pack["title"], quote=True)}">'
                         f'<div class="stage"><img loading="lazy" width="240" height="240" src="gifs/{name}" alt="{esc(label, quote=True)}"></div>'
                         f'<figcaption><strong>{esc(label)}</strong><span>{esc(pack["title"])}</span>'
                         f'<small>{esc(note or status)}</small><a class="icon-button download" href="gifs/{name}" download title="下载 GIF" aria-label="下载 {esc(label, quote=True)}">{icon("download")}</a></figcaption></figure>')
    esc = html.escape
    options = '<option value="">全部系列</option>' + ''.join(f'<option value="{p["id"]}">{esc(p["title"])}</option>' for p in packs)
    navigation = ''.join(f'<button class="pack-button" data-choose-pack="{p["id"]}" data-group="{p["group"]}" title="{esc(p["title"], quote=True)}">'
                         f'<img loading="lazy" src="{p.get("preview", "")}" alt="" width="42" height="42"><span>{esc(p["title"])}<small>{esc(p["status"])}</small></span><b>{p["count"]}</b></button>' for p in packs)
    current = [p for p in packs if p['group'] == 'current']
    page = Path(__file__).with_name('sticker_library.html').read_text(encoding='utf-8')
    replacements = {'TITLE': esc(config.get('title', '四位伙伴 · 表情收藏室')), 'CARDS': ''.join(cards), 'NAV': navigation,
                    'OPTIONS': options, 'SERIES_COUNT': str(len(current)), 'STICKER_COUNT': str(sum(p['count'] for p in current)),
                    'PACK_DATA': json.dumps(packs, ensure_ascii=False).replace('<', '\\u003c'),
                    'VIEWER': viewer_markup(), 'SEARCH_ICON': icon('search'), 'GRID_ICON': icon('grid'), 'ZOOM_ICON': icon('zoom')}
    for key, value in replacements.items():
        page = page.replace('__' + key + '__', value)
    (output / 'index.html').write_text(page, encoding='utf-8')
    (output / 'LICENSE-icons.txt').write_text(LICENSE)
    audit = {'packs': packs, 'gif_count': len(reports), 'files': reports, 'public_export': public_only}
    (output / 'audit.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return {'pack_count': len(packs), 'gif_count': len(reports), 'public_export': public_only}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('config', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--archive-root', type=Path)
    parser.add_argument('--public-only', action='store_true', help='Only explicitly approved public packs; no deployment')
    args = parser.parse_args()
    if args.public_only and args.output.exists() and any(args.output.iterdir()):
        parser.error('Public export requires a new empty destination, to avoid leaking old review assets')
    print(json.dumps(build(json.loads(args.config.read_text()), args.output, args.archive_root, args.public_only), ensure_ascii=False))


if __name__ == '__main__':
    main()
