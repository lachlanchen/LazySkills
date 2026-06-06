---
applyTo: "skills/**,docs/**,scripts/**,README.md,AGENTS.md,CLAUDE.md,GEMINI.md,skills.json"
---

# LazySkills Instructions

This repository must remain platform-neutral. Support AgInTiFlow, Codex, Claude, Gemini, GitHub Copilot, and generic local-tool agents without hard-coding one runtime into every skill.

When changing skills:

- Preserve `skills/<id>/SKILL.md` as the canonical agent-readable file.
- Keep frontmatter concise and scalar where possible.
- Put large examples or runbooks in `references/`.
- Prefer deterministic scripts for fragile browser, publishing, OCR, PDF, or validation steps.
- Update `skills.json` when adding, renaming, or removing a skill.
- Run `python3 scripts/lazyskills.py validate`.

When adding platform support:

- Add adapter instructions at the repo level.
- Do not duplicate platform instructions into every skill unless the skill genuinely needs that platform.
- Keep install commands token-safe and avoid printing secrets.
