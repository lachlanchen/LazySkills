#!/usr/bin/env python3
"""Find safe caption candidates without changing the source animation."""
import argparse
import json
import math
from pathlib import Path
import subprocess
import tempfile

from PIL import Image
from compact_wechat_sticker import motion_bbox, reframe, caption_layout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--label', required=True)
    parser.add_argument('--font', type=Path, required=True)
    parser.add_argument('--duration', type=float, default=5.125)
    parser.add_argument('--speed', type=float, default=1.25)
    parser.add_argument('--fps', type=int, default=15)
    args = parser.parse_args()
    if not args.source.is_file() or not args.font.is_file():
        parser.error('Source and font must exist')
    if (not args.label.strip() or not 1 <= args.fps <= 30 or
            not all(math.isfinite(x) and x > 0 for x in (args.duration, args.speed))):
        parser.error('Nonempty label and positive finite timing are required')
    with tempfile.TemporaryDirectory(prefix='sticker-caption-probe-') as temporary:
        subprocess.run(['ffmpeg', '-v', 'error', '-nostdin', '-threads', '2',
                        '-t', str(args.duration), '-i', str(args.source), '-vf',
                        f'setpts=(PTS-STARTPTS)/{args.speed},fps={args.fps}', '-threads', '2',
                        temporary + '/%04d.png'], check=True)
        frames = []
        for path in sorted(Path(temporary).glob('*.png')):
            with Image.open(path) as image:
                frames.append(image.convert('RGB'))
        if len(frames) < 2:
            raise SystemExit('Need at least two decoded frames')
        box = motion_bbox(frames)
        for padding in (1, 5, 10):
            framed = [reframe(frame, box, padding) for frame in frames]
            candidates = []
            for size in (24, 21, 18):
                for vertical, positions in (
                    (True, [(x, y) for x in (16, 22, 218, 224)
                            for y in (60, 80, 120, 160, 180)]),
                    (False, [(x, y) for x in (65, 120, 175)
                             for y in (18, 30, 210, 224)])):
                    for center in positions:
                        try:
                            item, overlap = caption_layout(framed, args.label,
                                args.font, size, center, vertical)
                        except ValueError:
                            continue
                        if overlap <= .02:
                            candidates.append({'padding': padding,
                                               'overlap': overlap, 'layout': item})
                if candidates:
                    print(json.dumps(sorted(candidates, key=lambda x: x['overlap'])[:5],
                                     ensure_ascii=False, indent=2))
                    return
        raise SystemExit('No safe candidate; inspect the art before changing layout.')


if __name__ == '__main__':
    main()
