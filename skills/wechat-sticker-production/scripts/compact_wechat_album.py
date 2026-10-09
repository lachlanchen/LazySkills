#!/usr/bin/env python3
"""Version an existing sticker album with edge layouts; never call a model."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

from audit_wechat_album import audit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Volume root containing native slug/slug.mp4 files")
    parser.add_argument("layout", type=Path, help="Existing caption layout JSON")
    parser.add_argument("packaging", type=Path, help="Approved independent album artwork")
    parser.add_argument("output", type=Path, help="Separate new edition; resumable")
    parser.add_argument("--font", required=True, type=Path)
    parser.add_argument("--gifsicle", type=Path)
    args = parser.parse_args()
    config = json.loads(args.layout.read_text())
    items = config["items"]
    if args.output.resolve() in {args.source.resolve(), args.packaging.resolve()}:
        parser.error("Output must be a separate edition")
    args.output.mkdir(parents=True, exist_ok=True)
    gifs = args.output / "gifs"
    gifs.mkdir(exist_ok=True)
    logs = args.output / "export-logs"
    logs.mkdir(exist_ok=True)
    for name in ("cover.png", "icon.png", "banner.jpg", "reward-guide.png", "reward-thanks.png"):
        source, dest = args.packaging / name, args.output / name
        if dest.exists() and dest.read_bytes() != source.read_bytes():
            raise ValueError(f"Packaging changed: {name}")
        if not dest.exists():
            shutil.copy2(source, dest)
    results = []
    for item in items:
        slug = Path(item["file"]).stem
        source = args.source / slug / (slug + ".mp4")
        output = gifs / (slug + ".gif")
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        if output.exists():
            report = json.loads(output.with_suffix(".json").read_text())
            if report["source_sha256"] != digest or report["layout"]["label"] != item["label"]:
                raise ValueError(f"Changed input for existing export: {slug}")
            audit(output)
        else:
            success = False
            for size in (24, 21, 18):
                command = [sys.executable, str(Path(__file__).with_name("compact_wechat_sticker.py")),
                           str(source), str(output), "--label", item["label"], "--font", str(args.font),
                           "--padding", "1", "--font-size", str(size)]
                if args.gifsicle:
                    command += ["--gifsicle", str(args.gifsicle)]
                result = subprocess.run(command, text=True, capture_output=True)
                log = logs / f"{slug}-font{size}.txt"
                if log.exists():
                    log = logs / f"{slug}-font{size}-resume.txt"
                    if log.exists():
                        raise ValueError("Repeated failure; inspect existing evidence before another attempt")
                log.write_text(result.stdout + result.stderr)
                if result.returncode == 0:
                    success = True
                    break
                if output.exists():
                    raise ValueError(f"Partial output exists: {slug}")
            if not success:
                results.append({"file": output.name, "status": "needs_local_layout_revision"})
                print(json.dumps(results[-1]), flush=True)
                continue
            report = json.loads(output.with_suffix(".json").read_text())
            audit(output)
        results.append({"file": output.name, "label": item["label"], "status": "exported_needs_visual_review",
                        "bytes": output.stat().st_size, "layout": report["layout"],
                        "source_sha256": digest})
        print(json.dumps(results[-1], ensure_ascii=False), flush=True)
        (args.output / "progress.json").write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n")
    (args.output / "progress.json").write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n")
    if any(result["status"] == "needs_local_layout_revision" for result in results):
        raise SystemExit("Some files need local export adjustment; no generation was repeated")
    subprocess.run([sys.executable, str(Path(__file__).with_name("audit_wechat_album.py")), str(args.output),
                    "--expected", str(len(items)), "--title", config["title"].split(" · ")[0] + " · 贴边版"], check=True)


if __name__ == "__main__":
    main()
