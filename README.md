[English](README.md) · [简体中文](i18n/README.zh-CN.md) · [繁體中文](i18n/README.zh-TW.md) · [日本語](i18n/README.ja.md) · [한국어](i18n/README.ko.md) · [Français](i18n/README.fr.md) · [Español](i18n/README.es.md) · [Deutsch](i18n/README.de.md) · [Italiano](i18n/README.it.md) · [Português](i18n/README.pt-BR.md) · [Русский](i18n/README.ru.md) · [العربية](i18n/README.ar.md)

# LazySkills

[![Agent Skills](https://img.shields.io/badge/agent--skills-portable-6f42c1)](docs/platform-support.md)
[![Browser Automation](https://img.shields.io/badge/browser--automation-CDP-0969da)](docs/xyq-browser-video-publishing.md)
[![LazyingArt](https://img.shields.io/badge/LazyingArt-lazying.art-111111)](https://lazying.art)
[![GitHub Sponsors](https://img.shields.io/badge/Sponsor-lachlanchen-ea4aaa?style=for-the-badge&logo=githubsponsors&logoColor=white)](https://github.com/sponsors/lachlanchen)

Portable skills for agents that need to act, verify, and finish real work.

LazySkills is a reusable skill library by [lachlanchen](https://github.com/lachlanchen) for the LazyingArt ecosystem. It packages proven workflows as compact `SKILL.md` playbooks with optional scripts, references, and validation methods.

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
| `media-transcription-report` | Transcribes audio or video into timestamped Markdown with optional WhisperX speaker diarization, then turns transcripts or source notes into neutral third-person Markdown/TeX/PDF reports. | Whisper, WhisperX, ffmpeg, speaker diarization, Markdown, XeLaTeX/PDF compilation |
| `npm-publishing` | Packages, publishes, and verifies npm packages while handling 2FA, token files, trusted publishing, and install smoke tests safely. | npm, GitHub Actions OIDC, temp `.npmrc`, registry verification |
| `ocr-book-polisher` | Converts scanned or image-heavy books into corrected, publishable Markdown/TeX/PDF while preserving figures, captions, structure, and evidence checks. | OCR, page-aware Markdown, strict TOC validation, TeX/PDF compilation |
| `pocketpolyglot-bookmaker` | Builds LinguaLeaf/PocketPolyglot-style multilingual interlinear pocket books with durable JSON, ruby/pinyin/furigana, grammar roles, and bidirectional PDFs. | EPUB/PDF extraction, chunk manifests, JSON validation, tmux workers, XeLaTeX |

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

Preferred no-copy external pack use:

```bash
export AGINTIFLOW_SKILL_PACKS="/home/lachlan/ProjectsLFS/LazySkills"
aginti skills "npm publishing"
aginti skills "PocketPolyglot"
```

Project-local copy when a single project needs pinned/customized skills:

```bash
cd /path/to/project
python3 /home/lachlan/ProjectsLFS/LazySkills/scripts/lazyskills.py install --platform aginti --scope project npm-publishing
aginti skills "npm publishing"
```

SkillMesh import still works when you want reviewed/enabled SkillMesh copies. Example for `npm-publishing`:

```bash
cd /home/lachlan/ProjectsLFS/Agent/AgInTiFlow
node --input-type=module - <<'NODE'
import fs from "node:fs/promises";
import {
  buildSkillPackFromMarkdown,
  enableSkillMeshSkill,
  installSkillPack,
} from "./src/skillmesh.js";

const content = await fs.readFile("/home/lachlan/ProjectsLFS/LazySkills/skills/npm-publishing/SKILL.md", "utf8");
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
cp -R skills/ocr-book-polisher ~/.codex/skills/
cp -R skills/pocketpolyglot-bookmaker ~/.codex/skills/
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
test -f skills/ocr-book-polisher/SKILL.md
test -f skills/pocketpolyglot-bookmaker/SKILL.md
aginti skills "npm publishing"
```

## Documentation

- [Platform support](docs/platform-support.md)
- [Xiaoyunque browser video publishing](docs/xyq-browser-video-publishing.md)
- [Smooth Xiaoyunque video generation runbook](skills/lalachan-xyq-browser-video/references/smooth-video-generation-runbook.md)
- [LazyEdit publish runbook](docs/lazyedit-publish-runbook.md)
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
