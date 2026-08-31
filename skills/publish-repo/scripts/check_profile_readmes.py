#!/usr/bin/env python3
"""Validate the structural contract for Lachlanchen profile-style READMEs."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


ROOT_HEADER = (
    "[English](README.md) · [العربية](i18n/README.ar.md) · "
    "[Español](i18n/README.es.md) · [Français](i18n/README.fr.md) · "
    "[日本語](i18n/README.ja.md) · [한국어](i18n/README.ko.md) · "
    "[Tiếng Việt](i18n/README.vi.md) · [中文 (简体)](i18n/README.zh-Hans.md) · "
    "[中文（繁體）](i18n/README.zh-Hant.md) · [Deutsch](i18n/README.de.md) · "
    "[Русский](i18n/README.ru.md)"
)
I18N_HEADER = (
    "[English](../README.md) · [العربية](README.ar.md) · "
    "[Español](README.es.md) · [Français](README.fr.md) · "
    "[日本語](README.ja.md) · [한국어](README.ko.md) · "
    "[Tiếng Việt](README.vi.md) · [中文 (简体)](README.zh-Hans.md) · "
    "[中文（繁體）](README.zh-Hant.md) · [Deutsch](README.de.md) · "
    "[Русский](README.ru.md)"
)
TRANSLATIONS = (
    "README.ar.md",
    "README.es.md",
    "README.fr.md",
    "README.ja.md",
    "README.ko.md",
    "README.vi.md",
    "README.zh-Hans.md",
    "README.zh-Hant.md",
    "README.de.md",
    "README.ru.md",
)
REQUIRED_FRAGMENTS = (
    "LazyingArt banner",
    "| Donate | PayPal | Stripe |",
    "https://chat.lazying.art/donate",
    "https://paypal.me/RongzhouChen",
    "https://buy.stripe.com/aFadR8gIaflgfQV6T4fw400",
    "https://github.com/sponsors/lachlanchen",
    "CITATION.cff",
    "@software",
)
STABLE_FENCE_LANGUAGES = {"bash", "sh", "shell", "console", "bibtex"}
FENCE_PATTERN = re.compile(r"^```([^\n]*)\n(.*?)^```\s*$", re.MULTILINE | re.DOTALL)


def first_content_line(text: str) -> str:
    return next((line for line in text.splitlines() if line.strip()), "")


def stable_fences(text: str) -> list[tuple[str, str]]:
    blocks: list[tuple[str, str]] = []
    for match in FENCE_PATTERN.finditer(text):
        language = match.group(1).strip().lower()
        if language in STABLE_FENCE_LANGUAGES:
            blocks.append((language, match.group(2).strip()))
    return blocks


def heading_count(text: str) -> int:
    return len(re.findall(r"^##\s+", text, flags=re.MULTILINE))


def prose_size(text: str) -> int:
    without_fences = FENCE_PATTERN.sub("", text)
    without_urls = re.sub(r"https?://\S+", "", without_fences)
    return sum(character.isalnum() for character in without_urls)


def validate(repo: Path) -> list[str]:
    errors: list[str] = []
    root_path = repo / "README.md"
    funding_path = repo / ".github" / "FUNDING.yml"
    citation_path = repo / "CITATION.cff"

    for required in (root_path, funding_path, citation_path):
        if not required.is_file():
            errors.append(f"missing required file: {required.relative_to(repo)}")
    if not root_path.is_file():
        return errors

    root_text = root_path.read_text(encoding="utf-8")
    if first_content_line(root_text) != ROOT_HEADER:
        errors.append("README.md does not start with the exact 11-language header")
    for fragment in REQUIRED_FRAGMENTS:
        if fragment not in root_text:
            errors.append(f"README.md is missing required profile element: {fragment}")

    root_fences = stable_fences(root_text)
    root_headings = heading_count(root_text)
    root_prose_size = max(prose_size(root_text), 1)

    for name in TRANSLATIONS:
        path = repo / "i18n" / name
        if not path.is_file():
            errors.append(f"missing translation: i18n/{name}")
            continue
        text = path.read_text(encoding="utf-8")
        label = f"i18n/{name}"
        if first_content_line(text) != I18N_HEADER:
            errors.append(f"{label} does not start with the exact 11-language header")
        for fragment in REQUIRED_FRAGMENTS:
            if fragment not in text:
                errors.append(f"{label} is missing required profile element: {fragment}")
        if stable_fences(text) != root_fences:
            errors.append(f"{label} command/BibTeX blocks differ from README.md")
        if heading_count(text) != root_headings:
            errors.append(
                f"{label} has {heading_count(text)} level-two sections; README.md has {root_headings}"
            )
        if text == root_text:
            errors.append(f"{label} is an untranslated copy of README.md")
        # CJK prose can express the same content with materially fewer Unicode
        # alphanumeric code points than English, so keep this only as a coarse
        # truncation guard. Stable blocks and section parity catch structural drift.
        if prose_size(text) < root_prose_size * 0.45:
            errors.append(f"{label} has too little prose to represent the full README")

    if funding_path.is_file():
        funding = funding_path.read_text(encoding="utf-8")
        for fragment in ("github: [lachlanchen]", "https://github.com/sponsors/lachlanchen"):
            if fragment not in funding:
                errors.append(f".github/FUNDING.yml is missing: {fragment}")

    if citation_path.is_file():
        citation = citation_path.read_text(encoding="utf-8")
        for fragment in ("cff-version:", "type: software", "repository-code:"):
            if fragment not in citation:
                errors.append(f"CITATION.cff is missing: {fragment}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check the synchronized 11-language Lachlanchen README contract."
    )
    parser.add_argument("repo", nargs="?", default=".", help="repository root (default: current directory)")
    args = parser.parse_args()
    repo = Path(args.repo).expanduser().resolve()
    errors = validate(repo)
    if errors:
        print("profile README checks failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("profile README checks passed (English + 10 translations)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
