#!/usr/bin/env python3
"""Read-only three-way source planning and scoped post-upload verification."""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path, PurePosixPath
import stat
import subprocess
import sys
import tempfile
import zipfile


LIMIT = 512 * 1024 * 1024
TEXT_SUFFIXES = {".tex", ".bib", ".sty", ".cls", ".bst", ".txt", ".md", ".csv"}


def safe_name(name):
    if not isinstance(name, str) or not name or "\\" in name or ":" in name:
        raise ValueError(f"Invalid project-relative path: {name!r}")
    path = PurePosixPath(name)
    if path.is_absolute() or any(p in {"", ".", ".."} for p in name.split("/")):
        raise ValueError(f"Unsafe project-relative path: {name!r}")
    return name


def digest(data):
    return hashlib.sha256(data).hexdigest() if data is not None else None


def snapshot(source):
    """Read a source ZIP/directory without extracting it or following symlinks."""
    source = Path(source)
    result, seen, total = {}, set(), 0
    if source.is_dir():
        for path in sorted(source.rglob("*")):
            if path.is_symlink():
                raise ValueError(f"Snapshot symlink rejected: {path}")
            if path.is_dir():
                continue
            if not path.is_file():
                raise ValueError(f"Nonregular snapshot entry: {path}")
            total += path.stat().st_size
            if total > LIMIT:
                raise ValueError("Snapshot exceeds 512 MiB uncompressed")
            result[safe_name(path.relative_to(source).as_posix())] = path.read_bytes()
    else:
        with zipfile.ZipFile(source) as archive:
            for item in archive.infolist():
                name = safe_name(item.filename.rstrip("/") if item.is_dir() else item.filename)
                if name in seen:
                    raise ValueError(f"Duplicate ZIP entry: {name}")
                seen.add(name)
                mode = item.external_attr >> 16
                kind = stat.S_IFMT(mode)
                if kind not in {0, stat.S_IFREG, stat.S_IFDIR}:
                    raise ValueError(f"Nonregular ZIP entry: {name}")
                if item.is_dir():
                    continue
                total += item.file_size
                if total > LIMIT:
                    raise ValueError("Snapshot exceeds 512 MiB uncompressed")
                result[name] = archive.read(item)
    # A file cannot also be an ancestor of another file.
    for name in result:
        if any(str(p) in result for p in PurePosixPath(name).parents if str(p) != "."):
            raise ValueError(f"Conflicting snapshot paths: {name}")
    return result


def load_mapping(path):
    data = json.loads(Path(path).read_text()) if path else {}
    if not isinstance(data, dict) or set(data) - {"files", "local_to_remote_text"}:
        raise ValueError("Mapping supports only files and local_to_remote_text")
    files, rules = data.get("files", {}), data.get("local_to_remote_text", {})
    if not isinstance(files, dict) or not isinstance(rules, dict):
        raise ValueError("Mapping sections must be objects")
    for remote, local in files.items():
        safe_name(remote)
        safe_name(local)
    for name, replacements in rules.items():
        safe_name(name)
        if not isinstance(replacements, list):
            raise ValueError(f"Replacement rules must be a list: {name}")
        for rule in replacements:
            if (not isinstance(rule, dict) or set(rule) != {"local", "remote"}
                    or not all(isinstance(v, str) and v for v in rule.values())):
                raise ValueError(f"Expected nonempty local/remote literal strings: {name}")
    return files, rules


def local_bytes(root, relative):
    path = root / safe_name(relative)
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"Local mapping escapes manuscript root: {relative}")
    if not path.exists():
        return None
    if not path.is_file():
        raise ValueError(f"Local path is not a regular file: {relative}")
    if path.stat().st_size > LIMIT:
        raise ValueError(f"Local file exceeds 512 MiB: {relative}")
    return path.read_bytes()


def merge_text(name, base, local, remote):
    if PurePosixPath(name).suffix.lower() not in TEXT_SUFFIXES:
        return "conflict", None
    try:
        for content in (base, local, remote):
            if b"\0" in content:
                return "conflict", None
            content.decode("utf-8")
    except UnicodeDecodeError:
        return "conflict", None
    with tempfile.TemporaryDirectory(prefix="overleaf-merge-") as directory:
        paths = [Path(directory) / side for side in ("local", "base", "remote")]
        for path, content in zip(paths, (local, base, remote)):
            path.write_bytes(content)
        command = ["git", "merge-file", "--stdout", "--diff3",
                   "-L", "LOCAL", "-L", "BASE", "-L", "OVERLEAF", *map(str, paths)]
        result = subprocess.run(command, capture_output=True, timeout=30)
        # Git returns the conflict count, capped at 127; 128+ is an error.
        if result.returncode < 0 or result.returncode > 127:
            raise RuntimeError("git merge-file failed; inspect inputs and Git availability")
        return ("merge_review" if result.returncode == 0 else "conflict"), result.stdout


def classify(base, local, remote, has_base):
    if has_base and base is not None and (local is None or remote is None):
        return "review_missing"
    if local == remote:
        return "unchanged" if has_base and local == base else "converged"
    if not has_base:
        return "bootstrap_review"
    if local == base:
        return "pull"
    if remote == base:
        return "push"
    return "both_changed"


def plan(args):
    root = Path(args.local)
    if not root.is_dir():
        raise ValueError("--local must be a manuscript directory")
    base = snapshot(args.base) if args.base else {}
    remote = snapshot(args.remote)
    files, rules = load_mapping(args.map)
    names = sorted(set(base) | set(remote) | set(files))
    if set(rules) - set(names):
        raise ValueError("Text normalization refers to an unmapped/unknown file")
    local_names = [files.get(name, name) for name in names]
    if len(set(local_names)) != len(local_names):
        raise ValueError("Multiple remote paths map to the same local path")
    output = Path(args.out)
    if output.exists():
        raise ValueError("--out must be a fresh directory; preserve previous reports")
    rows, candidates = [], {}
    for name, relative in zip(names, local_names):
        b, r, local = base.get(name), remote.get(name), local_bytes(root, relative)
        if local is not None and name in rules:
            value = local.decode("utf-8")
            for rule in rules[name]:
                value = value.replace(rule["local"], rule["remote"])
            local = value.encode("utf-8")
        status = classify(b, local, r, args.base is not None)
        candidate = None
        if status == "both_changed":
            if b is None or local is None or r is None:
                status = "conflict"
            else:
                status, candidate = merge_text(name, b, local, r)
        row = {"remote_path": name, "local_path": relative, "status": status,
               "sha256": {"base": digest(b), "local": digest(local), "remote": digest(r)}}
        if candidate is not None:
            row["candidate"] = "candidates/" + name
            candidates[row["candidate"]] = candidate
        rows.append(row)
    report = {"schema_version": 1, "has_baseline": args.base is not None,
              "counts": dict(Counter(row["status"] for row in rows)), "files": rows}
    output.mkdir(parents=True, mode=0o700, exist_ok=False)
    for relative, content in candidates.items():
        path = output / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"report": str(output / "report.json"), "counts": report["counts"]}))
    return 0


def verify(args):
    before, after = snapshot(args.before), snapshot(args.after)
    allowed = {safe_name(name) for name in args.allow}
    changed = sorted(name for name in set(before) | set(after) if before.get(name) != after.get(name))
    expected = snapshot(args.expected) if args.expected else {}
    mismatches = sorted(name for name, content in expected.items() if after.get(name) != content)
    unexpected = sorted(set(changed) - allowed)
    result = {"ok": not unexpected and not mismatches, "changed": changed,
              "unexpected": unexpected, "expected_mismatches": mismatches,
              "expected_files_checked": len(expected)}
    print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    p = commands.add_parser("plan", help="Write a read-only three-way plan")
    p.add_argument("--base", help="Last verified common source ZIP/directory; omit for first sync")
    p.add_argument("--local", required=True, help="Local manuscript root")
    p.add_argument("--remote", required=True, help="Fresh Overleaf source ZIP/directory")
    p.add_argument("--map", help="JSON remote-to-local filenames and literal text normalization")
    p.add_argument("--out", required=True, help="New private directory for report/candidates")
    p.set_defaults(run=plan)
    v = commands.add_parser("verify", help="Check remote changes and staged expected bytes")
    v.add_argument("--before", required=True, help="Pre-upload source ZIP/directory")
    v.add_argument("--after", required=True, help="Post-upload source ZIP/directory")
    v.add_argument("--allow", action="append", default=[], help="Allowed changed remote path; repeat")
    v.add_argument("--expected", help="ZIP/directory containing expected final files in remote layout")
    v.set_defaults(run=verify)
    args = parser.parse_args()
    try:
        return args.run(args)
    except (OSError, ValueError, RuntimeError, zipfile.BadZipFile, subprocess.TimeoutExpired) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
