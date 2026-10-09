#!/usr/bin/env python3
"""Export a reviewed selection of native clips with new edge-layout captions."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

from audit_wechat_album import audit


def validate_items(items):
    names = set()
    for item in items:
        name = item.get("id", "")
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", name) or name in names:
            raise ValueError("Every item needs a unique filename-safe id")
        if not item.get("label", "").strip():
            raise ValueError("Every item needs a caption")
        names.add(name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--font", type=Path, required=True)
    parser.add_argument("--gifsicle", type=Path)
    parser.add_argument("--lossy", type=int, default=0)
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    validate_items(config["items"])
    root = args.config.resolve().parent
    args.output.mkdir(parents=True, exist_ok=True)
    logs = args.output / "export-logs"
    logs.mkdir(exist_ok=True)
    results = []
    for item in config["items"]:
        source = (root / item["source"]).resolve()
        output = args.output / "gifs" / (item["id"] + ".gif")
        if not source.is_file():
            results.append({"id": item["id"], "state": "source_missing"})
            continue
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        if output.exists():
            report = json.loads(output.with_suffix(".json").read_text())
            if report["source_sha256"] != digest or report["layout"]["label"] != item["label"]:
                raise ValueError("Existing output has different input; use a new edition")
            audit(output)
            results.append({"id": item["id"], "state": "preserved"})
            continue
        for size in item.get("sizes", [24, 21, 18]):
            command = [sys.executable, str(Path(__file__).with_name("compact_wechat_sticker.py")),
                       str(source), str(output), "--label", item["label"], "--font", str(args.font),
                       "--padding", str(item.get("padding", 1)), "--font-size", str(size)]
            if args.gifsicle:
                command += ["--gifsicle", str(args.gifsicle), "--lossy", str(args.lossy)]
            if item.get("center"):
                command += ["--center", *map(str, item["center"])]
            if item.get("vertical"):
                command += ["--vertical"]
            layout_key = hashlib.sha256(json.dumps(command, ensure_ascii=False).encode()).hexdigest()[:12]
            log = logs / f"{item['id']}-{size}-{layout_key}.txt"
            if log.exists():
                continue
            result = subprocess.run(command, capture_output=True, text=True)
            log.write_text(result.stdout + result.stderr)
            if result.returncode == 0:
                audit(output)
                break
            if output.exists():
                raise ValueError("Partial export exists; inspect before retrying")
        state = "exported_needs_review" if output.exists() else "needs_layout_revision"
        results.append({"id": item["id"], "state": state})
        print(json.dumps(results[-1]), flush=True)
    (args.output / "selection-progress.json").write_text(json.dumps(results, indent=2) + "\n")
    if any(item["state"] in {"source_missing", "needs_layout_revision"} for item in results):
        raise SystemExit("Incomplete selection; inspect progress. No model was called.")


if __name__ == "__main__":
    main()
