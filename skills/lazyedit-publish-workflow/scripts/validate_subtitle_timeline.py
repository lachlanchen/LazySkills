#!/usr/bin/env python3
"""Reject polished SRT files that silently changed the source ASR timeline."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


TIMING_RE = re.compile(
    r"^(\d{2}):(\d{2}):(\d{2})[,.](\d{3})\s+-->\s+"
    r"(\d{2}):(\d{2}):(\d{2})[,.](\d{3})"
)


@dataclass(frozen=True)
class Cue:
    start_ms: int
    end_ms: int
    text: str


def timestamp_ms(parts: tuple[str, ...]) -> int:
    hours, minutes, seconds, millis = (int(value) for value in parts)
    return (((hours * 60) + minutes) * 60 + seconds) * 1000 + millis


def parse_srt(path: Path) -> list[Cue]:
    content = path.read_text(encoding="utf-8-sig").replace("\r\n", "\n")
    cues: list[Cue] = []
    for block in re.split(r"\n\s*\n", content.strip()):
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        timing_index = next((i for i, line in enumerate(lines) if "-->" in line), None)
        if timing_index is None:
            continue
        match = TIMING_RE.match(lines[timing_index])
        if not match:
            raise ValueError(f"invalid timing in {path}: {lines[timing_index]}")
        groups = match.groups()
        cues.append(
            Cue(
                start_ms=timestamp_ms(groups[:4]),
                end_ms=timestamp_ms(groups[4:]),
                text=" ".join(lines[timing_index + 1 :]),
            )
        )
    if not cues:
        raise ValueError(f"no subtitle cues found in {path}")
    return cues


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify that polished SRT cue count/order/timestamps match source ASR."
    )
    parser.add_argument("source", type=Path, help="Source ASR SRT")
    parser.add_argument("polished", type=Path, help="Corrected/polished SRT")
    parser.add_argument("--tolerance-ms", type=int, default=50)
    args = parser.parse_args()

    source = parse_srt(args.source)
    polished = parse_srt(args.polished)
    errors: list[str] = []

    if len(source) != len(polished):
        errors.append(f"cue count changed: source={len(source)} polished={len(polished)}")

    for index, (before, after) in enumerate(zip(source, polished), start=1):
        start_delta = abs(before.start_ms - after.start_ms)
        end_delta = abs(before.end_ms - after.end_ms)
        if start_delta > args.tolerance_ms or end_delta > args.tolerance_ms:
            errors.append(
                f"cue {index} timing changed: "
                f"start_delta={start_delta}ms end_delta={end_delta}ms"
            )

    if errors:
        print("subtitle timeline validation failed", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(f"subtitle timeline valid: {len(source)} cues")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
