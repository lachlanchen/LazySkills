#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def read_lines(path: Path) -> list[str]:
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines()]
    return [line for line in lines if line and not line.startswith("#")]


def read_lyrics_segments(run_dir: Path) -> list[dict]:
    path = run_dir / "analysis" / "lyrics.json"
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("segments") or []


def read_chords(run_dir: Path) -> list[dict]:
    path = run_dir / "analysis" / "chords.csv"
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a Musia target-language localization package.")
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--target-language", default="zh-CN")
    parser.add_argument("--target-lines", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    run_dir = args.run_dir.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    target_lines = read_lines(args.target_lines)
    segments = read_lyrics_segments(run_dir)
    chords = read_chords(run_dir)

    phrase_items = []
    for index, line in enumerate(target_lines):
        source_segment = segments[index] if index < len(segments) else {}
        phrase_items.append(
            {
                "index": index,
                "target_language": args.target_language,
                "target_text": line,
                "start": source_segment.get("start"),
                "end": source_segment.get("end"),
                "source_text": source_segment.get("text", ""),
                "estimated_chinese_syllables": len(line.replace(" ", "")),
            }
        )

    target_text_yingmusic = "|".join(target_lines)
    request = {
        "id": f"{run_dir.name}-{args.target_language}",
        "melody_ref_path": str(run_dir / "stems" / "vocals.wav"),
        "timbre_ref_path": str(run_dir / "stems" / "vocals.wav"),
        "gen_text": target_text_yingmusic,
        "timbre_ref_text": " ".join(item.get("source_text", "") for item in phrase_items).strip(),
        "instrumental_path": str(run_dir / "stems" / "instrumental.wav"),
        "notes": "Use a consented timbre reference if original-singer cloning is not authorized.",
    }

    (output_dir / "target_lyrics.txt").write_text("\n".join(target_lines) + "\n", encoding="utf-8")
    (output_dir / "target_text_yingmusic.txt").write_text(target_text_yingmusic + "\n", encoding="utf-8")
    (output_dir / "target_lyrics.json").write_text(
        json.dumps(
            {
                "run_dir": str(run_dir),
                "target_language": args.target_language,
                "phrases": phrase_items,
                "chords_preview": chords[:64],
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    (output_dir / "yingmusic_request.jsonl").write_text(
        json.dumps(request, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (output_dir / "synthesis_status.md").write_text(
        "\n".join(
            [
                "# Synthesis Status",
                "",
                "Status: `localized_lyrics_complete`",
                "",
                "The target-language lyric package is ready. Final same-music sung audio still requires a singing synthesis backend such as YingMusic-Singer-Plus or SoulX-Singer with local model weights.",
                "",
                "Prepared inputs:",
                "",
                f"- Melody reference: `{run_dir / 'stems' / 'vocals.wav'}`",
                f"- Instrumental mix: `{run_dir / 'stems' / 'instrumental.wav'}`",
                "- Target text: `target_text_yingmusic.txt`",
                "- Batch request: `yingmusic_request.jsonl`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(output_dir)


if __name__ == "__main__":
    main()

