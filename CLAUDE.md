# LazySkills For Claude

This repository is a portable skill pack. Prefer the relevant `skills/<id>/SKILL.md` file as the task playbook.

## Selection Rule

1. Match the user request against `skills.json` and each `SKILL.md` frontmatter.
2. Read only the selected skill first.
3. Load that skill's `references/` files only when the task needs them.
4. Run bundled scripts instead of recreating fragile browser, media, OCR, publishing, or validation logic.
5. Do not claim completion until files, commands, UI state, or published artifacts are verified.

## Claude Usage

For Claude Code or compatible Claude agents, use one of these patterns:

- Open this repository as project context and ask Claude to follow the matching `skills/<id>/SKILL.md`.
- Copy selected folders into a Claude-readable skills directory, preserving the full folder structure.
- For project-specific use, vendor only the needed skill folder into the target project, not the whole repository.

## Safety

Do not copy secrets, cookies, `.env` files, generated videos, private browser profiles, or run artifacts into skills. Skills are reusable procedures, not private task logs.
