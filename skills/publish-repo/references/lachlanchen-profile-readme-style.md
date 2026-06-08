# Lachlanchen Profile-Style Repository README

Use this reference when a repo should look like Lachlan Chen's public profile/readme style.

## Language Header

Root README:

```markdown
[English](README.md) · [العربية](i18n/README.ar.md) · [Español](i18n/README.es.md) · [Français](i18n/README.fr.md) · [日本語](i18n/README.ja.md) · [한국어](i18n/README.ko.md) · [Tiếng Việt](i18n/README.vi.md) · [中文 (简体)](i18n/README.zh-Hans.md) · [中文（繁體）](i18n/README.zh-Hant.md) · [Deutsch](i18n/README.de.md) · [Русский](i18n/README.ru.md)
```

i18n README files:

```markdown
[English](../README.md) · [العربية](README.ar.md) · [Español](README.es.md) · [Français](README.fr.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Tiếng Việt](README.vi.md) · [中文 (简体)](README.zh-Hans.md) · [中文（繁體）](README.zh-Hant.md) · [Deutsch](README.de.md) · [Русский](README.ru.md)
```

## Banner

```markdown
[![LazyingArt banner](https://github.com/lachlanchen/lachlanchen/raw/main/figs/banner.png)](https://github.com/lachlanchen/lachlanchen/blob/main/figs/banner.png)
```

## Support Panel

```markdown
| Donate | PayPal | Stripe |
| --- | --- | --- |
| [![Donate](https://img.shields.io/badge/Donate-LazyingArt-0EA5E9?style=for-the-badge&logo=kofi&logoColor=white)](https://chat.lazying.art/donate) | [![PayPal](https://img.shields.io/badge/PayPal-RongzhouChen-00457C?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/RongzhouChen) | [![Stripe](https://img.shields.io/badge/Stripe-Donate-635BFF?style=for-the-badge&logo=stripe&logoColor=white)](https://buy.stripe.com/aFadR8gIaflgfQV6T4fw400) |
```

## FUNDING.yml

```yaml
# These are supported funding model platforms

# GitHub Sponsors (up to 4 usernames)
github: [lachlanchen]

# External platforms (fill in if/when you use them)
patreon:
open_collective:
ko_fi:
tidelift:
community_bridge:
liberapay:
issuehunt:
lfx_crowdfunding:
polar:
buy_me_a_coffee:
thanks_dev:

# Custom links (up to 4)
custom: [
  "https://github.com/sponsors/lachlanchen",
  "https://lazying.art",
  "https://chat.lazying.art",
  "https://onlyideas.art"
]
```

## CITATION.cff

GitHub shows a **Cite this repository** panel when `CITATION.cff` exists on the default branch. Use this template, then adjust title, version, abstract, authors, repository URL, and keywords.

```yaml
cff-version: 1.2.0
message: "If you use PROJECT_NAME, please cite this repository."
type: software
title: "PROJECT_NAME: SHORT_RESEARCH_OR_SOFTWARE_TITLE"
version: 0.1.0
date-released: YYYY-MM-DD
abstract: "One concise sentence describing the repository."
authors:
  - family-names: Chen
    given-names: Lachlan
    alias: lachlanchen
repository-code: "https://github.com/lachlanchen/PROJECT_NAME"
url: "https://lazying.art"
keywords:
  - open source
  - research
```

## Citation Block

Root README:

````markdown
## Citation

If you use PROJECT_NAME in research, cite the repository. GitHub reads [CITATION.cff](CITATION.cff) and shows a **Cite this repository** panel on the repo page.

```bibtex
@software{chen_projectname_YEAR,
  author = {Chen, Lachlan},
  title = {PROJECT_NAME: SHORT_RESEARCH_OR_SOFTWARE_TITLE},
  year = {YEAR},
  url = {https://github.com/lachlanchen/PROJECT_NAME}
}
```
````

i18n README files should translate the explanatory sentence and link to `../CITATION.cff`, but keep the BibTeX block stable.

## README Outline

Use a compact structure:

1. Language header.
2. LazyingArt banner.
3. Project title and one strong italic tagline.
4. Badges for website, key artifacts, and GitHub Sponsors.
5. One paragraph explaining what the repo is.
6. Donation panel.
7. Visual signal: screenshot, render, diagram, or asset when available.
8. System/project concept bullets.
9. Current contents table with paths.
10. Quick start commands.
11. Research/design baseline or architecture notes.
12. Build/test/validation commands.
13. Citation section linked to `CITATION.cff`.
14. Status and scope note.

Translate every section into all 10 i18n files. Keep command blocks, file paths, project names, and badge labels stable.
