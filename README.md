[English](README.md) Â· [ç®€ä½“ä¸­æ–‡](i18n/README.zh-CN.md) Â· [ç¹é«”ä¸­æ–‡](i18n/README.zh-TW.md) Â· [æ—¥æœ¬èªž](i18n/README.ja.md) Â· [í•œêµ­ì–´](i18n/README.ko.md) Â· [FranÃ§ais](i18n/README.fr.md) Â· [EspaÃ±ol](i18n/README.es.md) Â· [Deutsch](i18n/README.de.md) Â· [Italiano](i18n/README.it.md) Â· [PortuguÃªs](i18n/README.pt-BR.md) Â· [Ð ÑƒÑÑÐºÐ¸Ð¹](i18n/README.ru.md) Â· [Ø§Ù„Ø¹Ø±Ø¨ÙŠØ©](i18n/README.ar.md)

# LazySkills

[![Agent Skills](https://img.shields.io/badge/agent--skills-portable-6f42c1)](docs/platform-support.md)
[![Browser Automation](https://img.shields.io/badge/browser--automation-CDP-0969da)](docs/xyq-browser-video-publishing.md)
[![Website](https://img.shields.io/badge/website-lachlanchen.github.io%2FLazySkills-1e6b4d)](https://lachlanchen.github.io/LazySkills/)
[![LazyingArt](https://img.shields.io/badge/LazyingArt-lazying.art-111111)](https://lazying.art)
[![GitHub Sponsors](https://img.shields.io/badge/Sponsor-lachlanchen-ea4aaa?style=for-the-badge&logo=githubsponsors&logoColor=white)](https://github.com/sponsors/lachlanchen)

Portable skills for agents that need to act, verify, and finish real work.

LazySkills is a reusable skill library by [lachlanchen](https://github.com/lachlanchen) for the LazyingArt ecosystem. It packages proven workflows as compact `SKILL.md` playbooks with optional scripts, references, and validation methods.

Website: [lachlanchen.github.io/LazySkills](https://lachlanchen.github.io/LazySkills/)

LALACHAN daily story/video operators can start from
[docs/lalachan-story-video-generation-handoff.md](docs/lalachan-story-video-generation-handoff.md).

## Fast Start

```bash
git clone git@github.com:lachlanchen/LazySkills.git
cd LazySkills
python3 scripts/lazyskills.py validate
python3 scripts/lazyskills.py list
```

Use without copying in AgInTiFlow:

```bash
export AGINTIFLOW_SKILL_PACKS="$PWD"
aginti skills "npm publishing"
```

Install locally for Codex or Claude:

```bash
python3 scripts/lazyskills.py install --platform codex
python3 scripts/lazyskills.py install --platform claude
```

## Why LazySkills

Modern agents are strongest when they have reliable working memory outside the chat window: task-specific procedures, deterministic scripts, and evidence-based completion checks. LazySkills keeps those pieces organized so different agents can reuse the same operational knowledge instead of rediscovering it every session.

The repository is intentionally platform-neutral. A skill should be useful to AgInTi, Codex, Gemini, GitHub Copilot, Claude, or any local-tool agent harness that can read files and run commands.

## Supported Agents

| Platform | How to use LazySkills |
| --- | --- |
| AgInTi / AgInTiFlow | Prefer `AGINTIFLOW_SKILL_PACKS=/path/to/LazySkills`; copy to project `.aginti/skills/` only for project-local overrides. |
| Codex | Install folders into `~/.codex/skills/` with `scripts/lazyskills.py install --platform codex`. |
| Claude agents | Use `CLAUDE.md` as the repo entrypoint or copy folders into a Claude-readable skill directory. |
| Gemini agents | Use `GEMINI.md` as the repo entrypoint and `skills.json` for skill discovery. |
| GitHub Copilot agents | Use `.github/copilot-instructions.md` and `.github/instructions/lazyskills.instructions.md`. |
| Generic local-tool agents | Read `skills.json`, then the selected `skills/<id>/SKILL.md`, and run bundled scripts under normal policy. |

## Available Skills

| Skill | What it does | Key tools |
| --- | --- | --- |
| `lalachan-xyq-browser-video` | Generates and monitors Xiaoyunque videos through the logged-in browser UI, with visible validation before paid submission. | Chrome/CDP, upload verification, prompt fill, thread watcher, MP4 download fallback |
| `lazyedit-publish-workflow` | Publishes LazyEdit videos and AI-generated LALACHAN/RARACHAN videos through AutoPubMonitor and AutoPublish, including subtitle correction and queue monitoring. | LazyEdit CLI/API, AutoPubMonitor, `lazyingart` SSH, tmux, Shipinhao, YouTube, Instagram |
| `musia-lalachan-mv-workflow` | Creates song-first LALACHAN/Xiaoyunque MV handoffs from reviewed Musia tracks, including full-song story MVs, chorus/highlight cuts, and song-locked audio replacement. | Musia audio, Xiaoyunque prompts, timestamped MV segments, ffmpeg muxing, LazyEdit-ready outputs |
| `media-transcription-report` | Transcribes audio or video into timestamped Markdown with optional WhisperX speaker diarization, then turns transcripts or source notes into neutral third-person Markdown/TeX/PDF reports. | Whisper, WhisperX, ffmpeg, speaker diarization, Markdown, XeLaTeX/PDF compilation |
| `npm-publishing` | Packages, publishes, and verifies npm packages while handling 2FA, token files, trusted publishing, and install smoke tests safely. | npm, GitHub Actions OIDC, temp `.npmrc`, registry verification |
| `publish-repo` | Publishes local git repositories to GitHub with profile-style multilingual READMEs, LazyingArt banner/support panels, sponsors, citation metadata, safe commits, remote creation, homepage, description, and topics. | git, GitHub CLI, repo metadata, i18n README, funding config, CITATION.cff, Codex/AgInTi handoff |
| `ocr-book-polisher` | Converts scanned, image-heavy, technical, or music books into corrected Markdown/TeX/PDF while preserving figures, equations, tables, diagrams, captions, and source structure. | Mathpix, Marker/Surya, pix2tex, OMR/MusicXML, page-aware Markdown, strict TOC and TeX validation |
| `libgen-safe-book-browser` | Opens LibGen search/detail pages through Chrome/CDP while blocking Trip.com and ad redirects, with exact metadata and PDF > EPUB > other candidate selection. | LibGen API, Chrome/CDP Fetch interception, redirect guard |
| `pocketpolyglot-bookmaker` | Builds LinguaLeaf/PocketPolyglot-style multilingual interlinear pocket books with durable JSON, ruby/pinyin/furigana, grammar roles, and bidirectional PDFs. | EPUB/PDF extraction, chunk manifests, JSON validation, tmux workers, XeLaTeX |
| `transcript-video-section-splitter` | Transcribes videos, derives topic-based section boundaries, and splits edited or source videos into named clips with manifests. | Whisper/WhisperX, content sections, ffmpeg, clip manifest |
| `video-face-image-replacement` | Covers or replaces one or more detected video faces with supplied or generated image assets, including multi-person animal masks with stable identity tracking. | InsightFace/SCRFD, identity maps, RetinaFace/MediaPipe options, alpha compositing, ffmpeg |
| `aginti-agentlink` | Coordinates multiple agent sessions across machines, repos, tools, hardware, and APIs using safe handoffs and action contracts. | peer maps, handoff packets, private session mirrors, status probes, evidence bundles |
| `codex-session-recovery` | Diagnoses and recovers stalled or extremely slow Codex threads without rewriting private session state. | read-only inspection, private verified backup, app-server compaction, ownership checks, append-only verification |
| `kv260-metavision-lab` | Operates and maintains the AMD Kria KV260 + Prophesee Metavision lab, including desktop launchers, custom viewer, recording API, native viewer recovery, Windows X11 control center, and file transfer. | PetaLinux, Prophesee, Metavision, V4L2, X11/Matchbox, SSH X11, event recording |
| `kv260-windows-arduino` | Coordinates KV260 event recording with the Windows host and USB Arduino light controller, including LAN identity, COM-port checks, future Arduino APIs, and cross-session handoffs. | KV260 API, Windows SSH, Arduino CLI, COM ports, DualLampHI, private session mirrors |
| `kicad-mcp-pcb-design` | Installs and uses KiCad with MCP/agent automation to inspect old PCB projects, generate boards, save datasets, validate DRC, export Gerbers/STEP, and render previews. | KiCad 10, `kicad-cli`, `pcbnew`, MCP stdio, Gerber/STEP/render export |
| `jlceda-mcp-automation` | Installs, activates, launches, and wires JLCEDA/LCEDA Pro with MCP bridge automation for agent-controlled PCB design. | LCEDA Pro, Electron CDP, `hyl64/jlcmcp`, `jlc-bridge.eext`, gateway WebSocket, MCP validation |
| `dual-led-constant-power` | Calibrates and controls dual Arduino-driven LED branches with MOS modules and INA219 monitoring for smooth constant-power crossfades. | Arduino UNO, YYNMOS MOS, INA219, inverse LUT, CSV/PNG telemetry |
| `parametric-cad-design` | Designs, revises, validates, documents, and renders mechanical CAD parts, including Shapr3D/STEP source analysis, exact B-rep regeneration, optical holders, and measured print-fit compensation. | Shapr3D `.shapr`, STEP/Parasolid, OpenSCAD, CadQuery/build123d/OCP, FreeCAD, Blender, STEP/STL/DXF/SVG/PDF, mesh checks |

## Skill Anatomy

```text
skills/
  skill-name/
    SKILL.md        # trigger conditions and core workflow
    scripts/        # deterministic helpers for fragile steps
    references/     # deeper notes loaded only when needed
skills.json         # machine-readable skill inventory
AGENTS.md           # general/Codex-style repo instructions
CLAUDE.md           # Claude project instructions
GEMINI.md           # Gemini project instructions
.github/            # Copilot instructions and sponsorship metadata
docs/               # general workflow documentation
i18n/               # localized README summaries
```

This structure keeps the skill itself concise while still preserving the tools and details needed for hard tasks.

## Install

### AgInTiFlow

Local paths should live in an ignored local config file:

```bash
cp .config/lazyskills.env.example .config/lazyskills.local.env
$EDITOR .config/lazyskills.local.env
set -a
. .config/lazyskills.local.env
set +a
```

Preferred no-copy external pack use:

```bash
export AGINTIFLOW_SKILL_PACKS="$LAZYSKILLS_ROOT"
aginti skills "npm publishing"
aginti skills "PocketPolyglot"
```

Project-local copy when a single project needs pinned/customized skills:

```bash
cd /path/to/project
python3 $LAZYSKILLS_ROOT/scripts/lazyskills.py install --platform aginti --scope project npm-publishing
aginti skills "npm publishing"
```

SkillMesh import still works when you want reviewed/enabled SkillMesh copies. Example for `npm-publishing`:

```bash
cd $AGINTIFLOW_ROOT
node --input-type=module - <<'NODE'
import fs from "node:fs/promises";
import {
  buildSkillPackFromMarkdown,
  enableSkillMeshSkill,
  installSkillPack,
} from "./src/skillmesh.js";

const skillsRoot = process.env.LAZYSKILLS_ROOT;
if (!skillsRoot) throw new Error("Set LAZYSKILLS_ROOT before running this example.");
const content = await fs.readFile(`${skillsRoot}/skills/npm-publishing/SKILL.md`, "utf8");
const pack = await buildSkillPackFromMarkdown(content, { valueScore: 92 });
await installSkillPack(pack, { enabled: true });
await enableSkillMeshSkill("npm-publishing", true);
console.log(JSON.stringify({ ok: true, installedSkills: pack.skills.map((skill) => skill.id), packHash: pack.packHash }, null, 2));
NODE
```

### Codex

```bash
python3 scripts/lazyskills.py install --platform codex
```

Manual equivalent:

```bash
cp -R skills/lalachan-xyq-browser-video ~/.codex/skills/
cp -R skills/lazyedit-publish-workflow ~/.codex/skills/
cp -R skills/media-transcription-report ~/.codex/skills/
cp -R skills/npm-publishing ~/.codex/skills/
cp -R skills/publish-repo ~/.codex/skills/
cp -R skills/ocr-book-polisher ~/.codex/skills/
cp -R skills/pocketpolyglot-bookmaker ~/.codex/skills/
cp -R skills/transcript-video-section-splitter ~/.codex/skills/
cp -R skills/video-face-image-replacement ~/.codex/skills/
cp -R skills/aginti-agentlink ~/.codex/skills/
cp -R skills/codex-session-recovery ~/.codex/skills/
cp -R skills/kv260-metavision-lab ~/.codex/skills/
cp -R skills/kv260-windows-arduino ~/.codex/skills/
cp -R skills/kicad-mcp-pcb-design ~/.codex/skills/
cp -R skills/jlceda-mcp-automation ~/.codex/skills/
cp -R skills/dual-led-constant-power ~/.codex/skills/
cp -R skills/parametric-cad-design ~/.codex/skills/
```

### Claude, Gemini, Copilot, Generic Agents

- Claude: start from `CLAUDE.md`, then selected `skills/<id>/SKILL.md`.
- Gemini: start from `GEMINI.md`, then `skills.json`, then selected `SKILL.md`.
- GitHub Copilot: repository instructions live in `.github/copilot-instructions.md` and `.github/instructions/lazyskills.instructions.md`.
- Generic agents: use `skills.json` as the index and keep skill folder structure intact.

For folder-copy agents:

```bash
python3 scripts/lazyskills.py install --platform claude
python3 scripts/lazyskills.py install --platform generic --dest ./agent-skills npm-publishing
```

## Quick Validation

Check browser automation helpers and skill file layout before using them:

```bash
python3 scripts/lazyskills.py validate
python3 scripts/lazyskills.py list --json
python3 skills/lalachan-xyq-browser-video/scripts/xyq_cdp_browser.py --help
python3 skills/lalachan-xyq-browser-video/scripts/xyq_chrome/watch_thread_dom_download.py --help
sed -n '1,40p' skills/lazyedit-publish-workflow/SKILL.md
test -f skills/media-transcription-report/SKILL.md
test -f skills/npm-publishing/SKILL.md
test -f skills/publish-repo/SKILL.md
bash -n skills/publish-repo/scripts/publish_repo.sh
test -f skills/ocr-book-polisher/SKILL.md
test -f skills/pocketpolyglot-bookmaker/SKILL.md
test -f skills/transcript-video-section-splitter/SKILL.md
test -f skills/video-face-image-replacement/SKILL.md
test -f skills/aginti-agentlink/SKILL.md
test -f skills/codex-session-recovery/SKILL.md
python3 -m py_compile skills/codex-session-recovery/scripts/*.py
python3 skills/codex-session-recovery/scripts/test_codex_session_recovery.py
test -f skills/kv260-metavision-lab/SKILL.md
test -f skills/kv260-windows-arduino/SKILL.md
test -f skills/kicad-mcp-pcb-design/SKILL.md
test -f skills/jlceda-mcp-automation/SKILL.md
test -f skills/dual-led-constant-power/SKILL.md
test -f skills/parametric-cad-design/SKILL.md
bash -n skills/kv260-metavision-lab/scripts/kv260_metavision_probe.sh
bash -n skills/kv260-windows-arduino/scripts/fetch-windows-codex-session.sh
bash -n skills/kv260-windows-arduino/scripts/kv260-lab-status.sh
bash -n skills/kv260-windows-arduino/scripts/kv260-record-once.sh
bash -n skills/kv260-windows-arduino/scripts/windows-arduino-probe.sh
aginti skills "npm publishing"
```

## Documentation

- [LazySkills website source](website/)
- [Platform support](docs/platform-support.md)
- [Canonical shared browser runtime](docs/shared-browser-runtime.md)
- [Xiaoyunque browser video publishing](docs/xyq-browser-video-publishing.md)
- [Smooth Xiaoyunque video generation runbook](skills/lalachan-xyq-browser-video/references/smooth-video-generation-runbook.md)
- [Xiaoyunque continue confirmation and protected download runbook](skills/lalachan-xyq-browser-video/references/continue-confirm-download-runbook.md)
- [LazyEdit publish runbook](docs/lazyedit-publish-runbook.md)
- [Publish repo skill handoff](docs/publish-repo-skill-handoff.md)
- [Codex stalled-session recovery runbook](docs/codex-session-recovery.md)
- [Reusable language header](i18n/language-header.md)

Detailed, project-specific run logs should live in the project that produced them. LazySkills keeps only reusable procedures and general examples.

## Design Principles

- Keep skills small enough to load quickly.
- Put fragile operations into scripts instead of rewriting them repeatedly.
- Validate before claiming completion.
- Keep API keys, cookies, browser profiles, generated videos, and private run artifacts out of the repo.
- Prefer general methods over hard-coded one-off task state.

## LazyingArt

Built by Lachlan Chen for creative AI workflows across storytelling, multilingual publishing, browser agents, and practical automation.

Main site: [lazying.art](https://lazying.art)  
Creative goods: [buy.lazying.art](https://buy.lazying.art)

---

## Support

| Donate | PayPal | Stripe |
| --- | --- | --- |
| [![Donate](https://img.shields.io/badge/Donate-LazyingArt-0EA5E9?style=for-the-badge&logo=kofi&logoColor=white)](https://chat.lazying.art/donate) | [![PayPal](https://img.shields.io/badge/PayPal-RongzhouChen-00457C?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/RongzhouChen) | [![Stripe](https://img.shields.io/badge/Stripe-Donate-635BFF?style=for-the-badge&logo=stripe&logoColor=white)](https://buy.stripe.com/aFadR8gIaflgfQV6T4fw400) |

[![GitHub Sponsors](https://img.shields.io/badge/Sponsor-lachlanchen-ea4aaa?style=for-the-badge&logo=githubsponsors&logoColor=white)](https://github.com/sponsors/lachlanchen)
