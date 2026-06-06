#!/usr/bin/env python3
"""LazySkills validation and lightweight installer.

The script intentionally uses only the Python standard library so it can run on
fresh macOS, Linux, Windows, WSL, CI, and minimal agent sandboxes.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = REPO_ROOT / "skills"
MANIFEST_PATH = REPO_ROOT / "skills.json"
IGNORED_NAMES = {".DS_Store", "__pycache__", ".pytest_cache"}
SKILL_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}[a-z0-9]$")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_manifest() -> dict:
    return json.loads(read_text(MANIFEST_PATH))


def parse_frontmatter(path: Path) -> tuple[dict, str]:
    text = read_text(path)
    match = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n?", text, flags=re.S)
    if not match:
        raise ValueError(f"{path}: missing YAML frontmatter")
    meta: dict[str, object] = {}
    lines = match.group(1).splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        index += 1
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        scalar = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if not scalar:
            raise ValueError(f"{path}: invalid frontmatter line: {line}")
        key, value = scalar.group(1), scalar.group(2).strip()
        if value:
            meta[key] = value.strip("\"'")
            continue
        items: list[str] = []
        while index < len(lines) and re.match(r"^\s+-\s+", lines[index]):
            items.append(re.sub(r"^\s+-\s+", "", lines[index]).strip().strip("\"'"))
            index += 1
        meta[key] = items
    return meta, text[match.end() :]


def skill_dirs() -> list[Path]:
    return sorted(path for path in SKILLS_DIR.iterdir() if path.is_dir() and (path / "SKILL.md").exists())


def list_skills(args: argparse.Namespace) -> int:
    manifest = load_manifest()
    if args.json:
        print(json.dumps(manifest, ensure_ascii=False, indent=2))
        return 0
    for skill in manifest.get("skills", []):
        print(f"{skill['id']}\t{skill['path']}\t{skill.get('category', '')}")
    return 0


def validate(_: argparse.Namespace) -> int:
    errors: list[str] = []
    manifest = load_manifest()
    manifest_ids = {item.get("id") for item in manifest.get("skills", [])}
    actual_ids = {path.name for path in skill_dirs()}

    if manifest.get("skillsRoot") != "skills":
        errors.append("skills.json: skillsRoot must be 'skills'")
    if manifest_ids != actual_ids:
        errors.append(f"skills.json mismatch: manifest={sorted(manifest_ids)} actual={sorted(actual_ids)}")

    required_root_files = ["README.md", "AGENTS.md", "CLAUDE.md", "GEMINI.md", ".github/copilot-instructions.md"]
    for name in required_root_files:
        if not (REPO_ROOT / name).exists():
            errors.append(f"missing platform entrypoint: {name}")

    for skill_dir in skill_dirs():
        skill_id = skill_dir.name
        if not SKILL_ID_RE.match(skill_id):
            errors.append(f"{skill_id}: skill directory must be lowercase hyphen-case")
        skill_path = skill_dir / "SKILL.md"
        try:
            meta, body = parse_frontmatter(skill_path)
        except Exception as exc:
            errors.append(str(exc))
            continue
        name = str(meta.get("name") or meta.get("id") or "").strip()
        description = str(meta.get("description") or "").strip()
        if name != skill_id:
            errors.append(f"{skill_path}: frontmatter name/id must match directory name ({skill_id})")
        if len(description) < 40:
            errors.append(f"{skill_path}: description is too short for reliable routing")
        if not body.strip():
            errors.append(f"{skill_path}: body is empty")
        for script in (skill_dir / "scripts").rglob("*") if (skill_dir / "scripts").exists() else []:
            if script.is_file() and script.name not in IGNORED_NAMES:
                if script.suffix in {".py", ".sh"} and not os.access(script, os.R_OK):
                    errors.append(f"{script}: script is not readable")

    if errors:
        print(json.dumps({"ok": False, "errors": errors}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1
    print(json.dumps({"ok": True, "skills": sorted(actual_ids)}, ensure_ascii=False, indent=2))
    return 0


def resolve_target_root(platform: str, scope: str, dest: str | None) -> Path:
    if dest:
        return Path(dest).expanduser().resolve()
    home = Path.home()
    cwd = Path.cwd()
    if platform == "codex":
        return (home / ".codex" / "skills").resolve()
    if platform == "claude":
        return ((cwd / ".claude" / "skills") if scope == "project" else (home / ".claude" / "skills")).resolve()
    if platform == "aginti":
        if scope == "project":
            return (cwd / ".aginti" / "skills").resolve()
        return (home / ".aginti" / "skills").resolve()
    if platform == "generic":
        return (cwd / "agent-skills").resolve()
    raise ValueError(f"Unsupported install platform: {platform}")


def copy_skill(skill_id: str, target_root: Path) -> dict:
    source = SKILLS_DIR / skill_id
    if not source.exists():
        raise ValueError(f"Unknown skill: {skill_id}")
    target = target_root / skill_id
    if target.exists():
        shutil.rmtree(target)
    ignore = shutil.ignore_patterns(".DS_Store", "__pycache__", "*.pyc", "outputs", "Downloads")
    shutil.copytree(source, target, ignore=ignore)
    return {"id": skill_id, "source": str(source), "target": str(target)}


def install(args: argparse.Namespace) -> int:
    if args.platform == "aginti" and args.scope != "project" and not args.dest:
        print(
            "AgInTiFlow has no generic ~/.aginti/skills user loader. "
            "Use AGINTIFLOW_SKILL_PACKS=/path/to/LazySkills for no-copy use, "
            "or rerun with --scope project inside the target project.",
            file=sys.stderr,
        )
        return 2
    selected = args.skills or [path.name for path in skill_dirs()]
    target_root = resolve_target_root(args.platform, args.scope, args.dest)
    target_root.mkdir(parents=True, exist_ok=True)
    installed = [copy_skill(skill_id, target_root) for skill_id in selected]
    payload = {
        "ok": True,
        "platform": args.platform,
        "scope": args.scope,
        "targetRoot": str(target_root),
        "installed": installed,
    }
    if args.platform == "aginti":
        payload["note"] = "AgInTiFlow no-copy use: export AGINTIFLOW_SKILL_PACKS=/path/to/LazySkills"
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="LazySkills helper")
    sub = parser.add_subparsers(dest="command", required=True)

    list_parser = sub.add_parser("list", help="List skills")
    list_parser.add_argument("--json", action="store_true", help="Print skills.json")
    list_parser.set_defaults(func=list_skills)

    validate_parser = sub.add_parser("validate", help="Validate skill layout and manifest")
    validate_parser.set_defaults(func=validate)

    install_parser = sub.add_parser("install", help="Copy selected skills into an agent skill directory")
    install_parser.add_argument("--platform", choices=["aginti", "codex", "claude", "generic"], required=True)
    install_parser.add_argument("--scope", choices=["user", "project"], default="user")
    install_parser.add_argument("--dest", help="Override target root directory")
    install_parser.add_argument("skills", nargs="*", help="Skill ids to install; default installs all")
    install_parser.set_defaults(func=install)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args) or 0)


if __name__ == "__main__":
    raise SystemExit(main())
