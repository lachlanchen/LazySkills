# Repository Guidelines

## Project Structure & Module Organization

This repository stores reusable agent skills and workflow documentation for AgInTi, Codex, Gemini, GitHub Copilot, Claude, and compatible local-tool agent harnesses.

- `skills/` contains installable skill folders. Each skill must include a `SKILL.md`.
- `skills/*/scripts/` contains executable helpers bundled with a skill.
- `skills/*/references/` contains detailed reference notes loaded only when needed.
- `skills.json` is the machine-readable skill inventory and must stay synchronized with `skills/`.
- `docs/` contains user-facing workflow documentation and run logs.
- `i18n/` contains localized README files.
- `docs/platform-support.md` explains how to adapt skills across supported agent platforms.
- `CLAUDE.md`, `GEMINI.md`, and `.github/copilot-instructions.md` are platform adapters, not canonical skill bodies.

## Build, Test, and Development Commands

There is no application build step. Validate scripts directly:

```bash
python3 scripts/lazyskills.py validate
python3 scripts/lazyskills.py list --json
python3 skills/lalachan-xyq-browser-video/scripts/xyq_cdp_browser.py --help
python3 skills/lalachan-xyq-browser-video/scripts/xyq_chrome/watch_thread_dom_download.py --help
sed -n '1,40p' skills/lazyedit-publish-workflow/SKILL.md
test -f skills/npm-publishing/SKILL.md
aginti skills "npm publishing"
```

Check Markdown and file layout manually before committing:

```bash
find skills docs i18n -type f | sort
```

## Coding Style & Naming Conventions

Use lowercase, hyphenated skill names, for example `lalachan-xyq-browser-video` or `lazyedit-publish-workflow`. Shell and Python scripts must accept explicit arguments and avoid hard-coded secrets. Markdown should be concise, task-oriented, and include runnable examples when useful.

When adding a skill, update `skills.json` and keep frontmatter `name` equal to the folder name. Use `description` as the primary routing text because most platforms see it before the body.

## Testing Guidelines

For browser automation scripts, test with `--help` first, then with a logged-in Chrome/CDP page. Verify outputs using screenshots, DOM evidence, and `ffprobe` for media files. Do not commit generated videos or private session artifacts.

## Commit & Pull Request Guidelines

Use short imperative commit messages, such as `Add Xiaoyunque browser skill` or `Document video publishing workflow`. Pull requests should include changed skill names, validation commands, and any relevant screenshots or run logs.

## Security & Configuration Tips

Never commit `.env`, cookies, tokens, or browser profiles. Document credential requirements without exposing values. Prefer browser-visible validation over hidden assumptions when submitting paid generation tasks.
