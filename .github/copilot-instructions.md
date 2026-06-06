# LazySkills Repository Instructions

LazySkills stores portable `SKILL.md` playbooks for multiple agent platforms. When working in this repository:

- Treat `skills/<id>/SKILL.md` as the canonical skill contract.
- Keep skill frontmatter compatible with broad agent loaders: `name` and `description` are required.
- Put platform-specific install details in `docs/`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, or `.github/instructions/`, not inside every skill.
- Keep bundled helper scripts deterministic and argument-driven.
- Do not commit secrets, cookies, browser profiles, generated media, private task logs, or `.env` files.
- Validate with `python3 scripts/lazyskills.py validate` before committing.

For task-specific agent behavior, choose the relevant skill using `skills.json`, then follow that skill's `SKILL.md`.
