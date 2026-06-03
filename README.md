# LazySkills

[English](README.md) · [简体中文](i18n/README.zh-CN.md) · [繁體中文](i18n/README.zh-TW.md) · [日本語](i18n/README.ja.md) · [한국어](i18n/README.ko.md) · [Français](i18n/README.fr.md) · [Español](i18n/README.es.md) · [Deutsch](i18n/README.de.md) · [Italiano](i18n/README.it.md) · [Português](i18n/README.pt-BR.md) · [Русский](i18n/README.ru.md) · [العربية](i18n/README.ar.md)

Reusable AI-agent skills, browser automation notes, and production workflows by [lachlanchen](https://github.com/lachlanchen) for the LazyingArt ecosystem.

LazySkills is a compact skill library for repeatable creative and engineering tasks. The first packaged skill is a browser-first Xiaoyunque video workflow for the LALACHAN series: it prepares prompts, uploads references, validates model settings, submits through Chrome/CDP, downloads protected output videos, and syncs them to local publishing folders.

## Skills

| Skill | Purpose |
| --- | --- |
| `lalachan-xyq-browser-video` | Generate and monitor Xiaoyunque videos through the logged-in browser UI, avoiding API submission unless explicitly requested. |

## Repository Layout

```text
skills/
  lalachan-xyq-browser-video/
    SKILL.md
    scripts/
    references/
docs/
  xyq-browser-video-publishing.md
  runs/
i18n/
```

## Use

Copy a skill folder into a Codex-compatible skills directory, or point your agent harness at this repository.

```bash
cp -R skills/lalachan-xyq-browser-video ~/.codex/skills/
```

The Xiaoyunque skill expects a logged-in Chrome window with CDP enabled and uses bundled scripts such as:

```bash
skills/lalachan-xyq-browser-video/scripts/xyq_cdp_browser.py --help
skills/lalachan-xyq-browser-video/scripts/xyq_chrome/watch_thread_dom_download.py --help
```

## Documentation

- [Xiaoyunque browser video publishing](docs/xyq-browser-video-publishing.md)
- [2026-06-03 typhoon ping-pong shark run](docs/runs/2026-06-03-typhoon-pingpong-shark.md)

## Profile

Built by Lachlan Chen for creative AI workflows across storytelling, multilingual publishing, browser agents, and practical automation.

Main site: [lazying.art](https://lazying.art)  
Shop and creative goods: [buy.lazying.art](https://buy.lazying.art)

---

### Support

If this repository helps your agent workflow, support the LazyingArt projects through [lazying.art](https://lazying.art) or [buy.lazying.art](https://buy.lazying.art).
