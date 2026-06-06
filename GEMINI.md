# LazySkills For Gemini

This repository is a portable skill pack for agents that can read Markdown and execute local helper scripts.

## How Gemini Should Use This Repo

1. Inspect `skills.json` to choose the smallest relevant skill.
2. Read `skills/<id>/SKILL.md`.
3. Use scripts under that skill's `scripts/` directory when available.
4. Load references only when the skill explicitly points to them and the current task needs them.
5. Validate concrete outputs before reporting success.

## Recommended Prompt

```text
Use the LazySkills repository as a portable skill pack. Select the relevant skill from skills.json, follow its SKILL.md, use bundled scripts where possible, and verify outputs before claiming completion.
```

## Notes

For Gemini CLI-style workflows, keep this `GEMINI.md` in the repository root so the repo itself provides the project-level operating contract.
