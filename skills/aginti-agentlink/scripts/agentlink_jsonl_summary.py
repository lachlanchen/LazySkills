#!/usr/bin/env python3
"""Summarize JSONL agent history without exposing full raw content."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path


def shorten(text: str, limit: int) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize agent JSONL history safely.")
    parser.add_argument("jsonl", type=Path, help="Path to JSONL history.")
    parser.add_argument("--pattern", default="", help="Regex for relevant entries.")
    parser.add_argument("--last", type=int, default=20, help="Number of matching entries to show.")
    parser.add_argument("--chars", type=int, default=220, help="Max characters per preview line.")
    args = parser.parse_args()

    rows = []
    with args.jsonl.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                rows.append({"_invalid": True, "text": line})

    sessions = Counter(str(row.get("session_id", "<missing>")) for row in rows)
    timestamps = [row.get("ts") for row in rows if isinstance(row.get("ts"), (int, float))]

    print(f"total_lines: {len(rows)}")
    print("sessions:")
    for session, count in sessions.most_common():
        print(f"  {session}: {count}")
    if timestamps:
        print(f"timestamp_range: {min(timestamps)}..{max(timestamps)}")

    if args.pattern:
        rx = re.compile(args.pattern, re.IGNORECASE)
        matches = [row for row in rows if rx.search(str(row.get("text", "")))]
        print(f"pattern: {args.pattern}")
        print(f"matches: {len(matches)}")
        print("recent_matches:")
        for row in matches[-args.last :]:
            session = row.get("session_id", "<missing>")
            ts = row.get("ts", "<missing>")
            text = shorten(str(row.get("text", "")), args.chars)
            print(f"  - [{session}] {ts}: {text}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

