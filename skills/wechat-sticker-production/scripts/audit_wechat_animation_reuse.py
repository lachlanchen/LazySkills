#!/usr/bin/env python3
"""Audit animation provenance across selected packs, ignoring lettering changes."""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path


def inspect(config, base):
    groups, items, missing = defaultdict(list), [], []
    for pack in config['packs']:
        if 'selection' in pack:
            selection = (base / pack['selection']).resolve()
            entries = json.loads(selection.read_text())['items']
            sources = [(entry['id'], entry['label'], selection.parent / entry['source']) for entry in entries]
        else:
            root = (base / pack['native_root']).resolve()
            gifs = (base / pack['gifs']).resolve()
            sources = []
            for gif in sorted(gifs.glob('*.gif')):
                sidecar = gif.with_suffix('.json')
                info = json.loads(sidecar.read_text()) if sidecar.exists() else {}
                label = info.get('label') or info.get('layout', {}).get('label') or gif.stem
                native = pack.get('overrides', {}).get(gif.stem, f'{gif.stem}/{gif.stem}.mp4')
                sources.append((gif.stem, label, root / native))
        if not sources:
            missing.append({'pack': pack['id'], 'reason': 'No selected source entries'})
        for item_id, label, source in sources:
            row = {'pack': pack['id'], 'id': item_id, 'label': label,
                   'source_filename': source.name, 'pack_state': pack.get('state', 'unknown')}
            if not source.is_file():
                missing.append(row)
                continue
            with source.open('rb') as file:
                digest = hashlib.file_digest(file, 'sha256').hexdigest()
            row['native_sha256'] = digest
            items.append(row)
            groups[digest].append(row)
    duplicates = [{'native_sha256': digest, 'items': rows} for digest, rows in groups.items() if len(rows) > 1]
    return {'passed': not duplicates and not missing, 'selected_count': len(items),
            'unique_native_count': len(groups), 'duplicate_extra_count': sum(len(g['items'])-1 for g in duplicates),
            'duplicate_groups': duplicates, 'missing': missing, 'items': items,
            'scope': 'Selected editions only; archived alternatives excluded. Native-file hashes catch caption/crop variants. Visual review remains required for separately encoded or similar actions.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('config', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Preserve earlier audit; select a new report path')
    report = inspect(json.loads(args.config.read_text()), args.config.resolve().parent)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({key:report[key] for key in ['passed','selected_count','unique_native_count','duplicate_extra_count','missing']}, ensure_ascii=False))
    raise SystemExit(0 if report['passed'] else 1)


if __name__ == '__main__':
    main()
