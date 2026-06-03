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

## AgInTiFlow SkillMesh Install

AgInTiFlow `0.20.191+` can import Codex-style `SKILL.md` files that use `name:` and `description:` frontmatter. It normalizes them to SkillMesh `id:` and `label:` metadata during import.

Install one LazySkills skill as a local-reviewed enabled SkillMesh skill:

```bash
cd /home/lachlan/ProjectsLFS/Agent/AgInTiFlow
export SKILL_PATH="/home/lachlan/ProjectsLFS/LazySkills/skills/npm-publishing/SKILL.md"
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
