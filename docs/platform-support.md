# Platform Support

LazySkills is written as a portable agent skill library rather than a single-tool-only package.

## Repository Contract

LazySkills supports two consumption modes:

- **External pack mode**: point an agent at the repository root and let it read `skills.json` plus selected `SKILL.md` files.
- **Copied skill mode**: copy one or more `skills/<id>/` folders into an agent-specific skill directory.

Do not flatten skill folders. Keep `SKILL.md`, `scripts/`, `references/`, and `assets/` together.

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
- `skills.json` gives a stable machine-readable inventory for agents that need discovery before reading Markdown bodies.
- `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, and `.github/` instruction files are adapters, not canonical skill content.

## How Agents Should Use It

1. Read the relevant `SKILL.md`.
2. Use bundled scripts instead of rewriting fragile automation.
3. Validate page state, files, costs, and outputs before claiming completion.
4. Load detailed references only when blocked or when the task needs deeper context.
5. Keep platform-specific glue outside the skill unless it is generally reusable.

## Platform Notes

Codex can install a skill folder directly into a skills directory. AgInTi can import the same folder as a custom skill or route it through its own skill mesh. Gemini, Copilot, and Claude agents can treat the folder as structured context plus tools, with the same validation checklist.

## Helper Script

Use the stdlib Python helper for repeatable validation and installation:

```bash
python3 scripts/lazyskills.py validate
python3 scripts/lazyskills.py list
python3 scripts/lazyskills.py install --platform codex
python3 scripts/lazyskills.py install --platform claude
python3 scripts/lazyskills.py install --platform aginti --scope project npm-publishing
```

The helper intentionally avoids third-party Python dependencies so it works in fresh macOS, Ubuntu, Windows/WSL, CI, and constrained agent environments.

## Platform Matrix

| Platform | Preferred mode | Entrypoint | Notes |
| --- | --- | --- | --- |
| AgInTiFlow | External pack | `AGINTIFLOW_SKILL_PACKS=/path/to/LazySkills` | Preserves the whole pack and shows source metadata in `aginti skills`. |
| AgInTiFlow project | Copied project skill | `.aginti/skills/<id>/SKILL.md` | Use only when a project needs a pinned or modified skill. |
| Codex | Copied skill | `~/.codex/skills/<id>/SKILL.md` | Use `python3 scripts/lazyskills.py install --platform codex`. |
| Claude | Repo or copied skill | `CLAUDE.md`, then `skills/<id>/SKILL.md` | Keep skill folders intact. |
| Gemini | Repo context | `GEMINI.md`, then `skills.json` | Use `skills.json` for discovery and selected `SKILL.md` for task behavior. |
| GitHub Copilot | Repo instructions | `.github/copilot-instructions.md` | Additional scoped instructions are in `.github/instructions/lazyskills.instructions.md`. |
| Generic local-tool agent | Repo or copied skill | `skills.json` | Select one skill, then read its `SKILL.md`; run scripts under the harness policy. |

## AgInTiFlow SkillMesh Install

AgInTiFlow `0.20.191+` can load LazySkills directly as an external pack:

```bash
AGINTIFLOW_SKILL_PACKS=$LAZYSKILLS_ROOT aginti skills
AGINTIFLOW_SKILL_PACKS=$LAZYSKILLS_ROOT aginti skills "OCR scanned book"
```

It can also import Codex-style `SKILL.md` files that use `name:` and `description:` frontmatter. It normalizes them to SkillMesh `id:` and `label:` metadata during import.

Install one LazySkills skill as a local-reviewed enabled SkillMesh skill:

```bash
cd $AGINTIFLOW_ROOT
export SKILL_PATH="$LAZYSKILLS_ROOT/skills/npm-publishing/SKILL.md"
export SKILL_ID="npm-publishing"
node --input-type=module - <<'NODE'
import fs from "node:fs/promises";
import {
  buildSkillPackFromMarkdown,
  enableSkillMeshSkill,
  installSkillPack,
} from "./src/skillmesh.js";

const source = process.env.SKILL_PATH;
const skillId = process.env.SKILL_ID;
const content = await fs.readFile(source, "utf8");
const pack = await buildSkillPackFromMarkdown(content, { valueScore: 92 });
await installSkillPack(pack, { enabled: true });
await enableSkillMeshSkill(skillId, true);
console.log(JSON.stringify({ ok: true, source, installedSkills: pack.skills.map((skill) => skill.id), packHash: pack.packHash }, null, 2));
NODE
```

Verify discovery and routing:

```bash
aginti skillmesh status
aginti skills "npm publishing"
aginti skills "GitHub Actions trusted npm publishing provenance"
```

The expected result includes `npm-publishing ... source=skillmesh`.
