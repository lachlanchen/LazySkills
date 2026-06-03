# Platform Support

LazySkills is written as a portable agent skill library rather than a single-tool-only package.

## Supported Agent Platforms

The repository can be used by:

- AgInTi / AgInTiFlow
- Codex
- Gemini-based agents
- GitHub Copilot-style agents
- Claude-based agents
- Any agent harness that can read Markdown, inspect local files, and run shell/Python tools

## Portability Model

Each skill folder is a self-contained playbook:

- `SKILL.md` gives the core trigger conditions and workflow.
- `scripts/` contains deterministic helpers for fragile browser or media steps.
- `references/` stores longer notes that should be loaded only when the task needs them.
- Repo-level `docs/` records complete real runs, problems, fixes, and verification evidence.

## How Agents Should Use It

1. Read the relevant `SKILL.md`.
2. Use bundled scripts instead of rewriting fragile automation.
3. Validate page state, files, costs, and outputs before claiming completion.
4. Load detailed references only when blocked or when the task needs deeper context.
5. Keep platform-specific glue outside the skill unless it is generally reusable.

## Platform Notes

Codex can install a skill folder directly into a skills directory. AgInTi can import the same folder as a custom skill or route it through its own skill mesh. Gemini, Copilot, and Claude agents can treat the folder as structured context plus tools, with the same validation checklist.
