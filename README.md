# LazySkills

[![Agent Skills](https://img.shields.io/badge/agent--skills-portable-6f42c1)](docs/platform-support.md)
[![Browser Automation](https://img.shields.io/badge/browser--automation-CDP-0969da)](docs/xyq-browser-video-publishing.md)
[![LazyingArt](https://img.shields.io/badge/LazyingArt-lazying.art-111111)](https://lazying.art)

[English](README.md) · [简体中文](i18n/README.zh-CN.md) · [繁體中文](i18n/README.zh-TW.md) · [日本語](i18n/README.ja.md) · [한국어](i18n/README.ko.md) · [Français](i18n/README.fr.md) · [Español](i18n/README.es.md) · [Deutsch](i18n/README.de.md) · [Italiano](i18n/README.it.md) · [Português](i18n/README.pt-BR.md) · [Русский](i18n/README.ru.md) · [العربية](i18n/README.ar.md)

Portable skills for agents that need to act, verify, and finish real work.

LazySkills is a reusable skill library by [lachlanchen](https://github.com/lachlanchen) for the LazyingArt ecosystem. It packages proven workflows as compact `SKILL.md` playbooks with optional scripts, references, and validation methods.

## Why LazySkills

Modern agents are strongest when they have reliable working memory outside the chat window: task-specific procedures, deterministic scripts, and evidence-based completion checks. LazySkills keeps those pieces organized so different agents can reuse the same operational knowledge instead of rediscovering it every session.

The repository is intentionally platform-neutral. A skill should be useful to AgInTi, Codex, Gemini, GitHub Copilot, Claude, or any local-tool agent harness that can read files and run commands.

## Supported Agents

| Platform | How to use LazySkills |
| --- | --- |
| AgInTi / AgInTiFlow | Import a skill folder as a custom skill or route it through a skill mesh. |
| Codex | Copy a skill folder into a Codex skills directory and use `SKILL.md` directly. |
| Gemini agents | Load `SKILL.md` as the workflow guide and call bundled scripts as tools. |
| GitHub Copilot agents | Use the repo as task context plus executable helper scripts. |
| Claude agents | Treat each skill folder as a structured playbook with validation checklists. |

## Available Skills

| Skill | What it does | Key tools |
| --- | --- | --- |
| `lalachan-xyq-browser-video` | Generates and monitors Xiaoyunque videos through the logged-in browser UI, with visible validation before paid submission. | Chrome/CDP, upload verification, prompt fill, thread watcher, MP4 download fallback |
| `lazyedit-publish-workflow` | Publishes LazyEdit videos and AI-generated LALACHAN/RARACHAN videos through AutoPubMonitor and AutoPublish, including subtitle correction and queue monitoring. | LazyEdit CLI/API, AutoPubMonitor, `lazyingart` SSH, tmux, Shipinhao, YouTube, Instagram |
| `npm-publishing` | Packages, publishes, and verifies npm packages while handling 2FA, token files, trusted publishing, and install smoke tests safely. | npm, GitHub Actions OIDC, temp `.npmrc`, registry verification |

## Skill Anatomy

```text
skills/
  skill-name/
    SKILL.md        # trigger conditions and core workflow
    scripts/        # deterministic helpers for fragile steps
    references/     # deeper notes loaded only when needed
docs/               # general workflow documentation
i18n/               # localized README summaries
```

This structure keeps the skill itself concise while still preserving the tools and details needed for hard tasks.

## Install

For Codex-style skill loading:

```bash
cp -R skills/lalachan-xyq-browser-video ~/.codex/skills/
cp -R skills/lazyedit-publish-workflow ~/.codex/skills/
cp -R skills/npm-publishing ~/.codex/skills/
```

For other agents, point the agent at this repository or copy the relevant `skills/<name>/` folder into that agent's custom-skill directory.

## Quick Validation

Check browser automation helpers and skill file layout before using them:

```bash
python3 skills/lalachan-xyq-browser-video/scripts/xyq_cdp_browser.py --help
python3 skills/lalachan-xyq-browser-video/scripts/xyq_chrome/watch_thread_dom_download.py --help
sed -n '1,40p' skills/lazyedit-publish-workflow/SKILL.md
test -f skills/npm-publishing/SKILL.md
```

## Documentation

- [Platform support](docs/platform-support.md)
- [Xiaoyunque browser video publishing](docs/xyq-browser-video-publishing.md)
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

### Support

If this repository helps your agent workflow, support the LazyingArt projects through [lazying.art](https://lazying.art) or [buy.lazying.art](https://buy.lazying.art).
