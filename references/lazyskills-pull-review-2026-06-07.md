# LazySkills Pull Review

Date: 2026-06-07  
Reviewer: Codex  
Repository: `/home/lachlan/ProjectsLFS/LazySkills`  
Review baseline: `c0e2832 Enable GitHub Pages deployment`  
Reviewed HEAD: `8947f70 Add KV260 Metavision lab skills`

## Purpose

Document the repository state after pulling updates made from other projects after the LazySkills website work.

The review covers:

- commits added after the website deployment baseline;
- current skill inventory;
- new skill purposes and design boundaries;
- validation executed;
- notable risks and follow-up work.

## Pull Result

Before pull, the local repo was clean and at:

```text
2b737084d23b39b1775e1b6119ff7ede5a9ea46b
```

`git pull --ff-only` fast-forwarded to:

```text
8947f70 Add KV260 Metavision lab skills
```

The repository remained clean after pull.

## Commits Since The Website Baseline

The last known point from the website session was:

```text
c0e2832 Enable GitHub Pages deployment
```

Commits added after that point:

```text
8947f70 Add KV260 Metavision lab skills
0bc9733 Add AgInTi AgentLink collaboration skill
2b73708 Add keyframe RGB mask propagation workflow
ff161e5 Document multi-person animal face masks
7206020 document LazyEdit logo publish rule
2cf4584 Document local section clip publishing
c31886c update LazyEdit publish workflow skill
02c45aa Clarify variant video section splitting
f54b7fc Improve face image replacement alpha guidance
76a1fdd Add video face replacement and transcript splitter skills
003eb02 clarify subtitle correction judgment
204ccb4 Add publish repo skill
```

Aggregate diff from `c0e2832` to `8947f70`:

```text
37 files changed, 3571 insertions(+), 5 deletions(-)
```

## Current Skill Inventory

`python3 scripts/lazyskills.py validate` reports 12 valid skills:

```text
aginti-agentlink
kv260-metavision-lab
kv260-windows-arduino
lalachan-xyq-browser-video
lazyedit-publish-workflow
media-transcription-report
npm-publishing
ocr-book-polisher
pocketpolyglot-bookmaker
publish-repo
transcript-video-section-splitter
video-face-image-replacement
```

The machine-readable catalog is `skills.json`.

## New And Expanded Skills

### `publish-repo`

Purpose:

Publish a clean local git repository to GitHub with `gh`, including remote creation, branch push, homepage, description, and topic metadata.

Important design points:

- refuses dirty worktrees;
- requires `git` and `gh`;
- checks `gh auth status`;
- refuses remote mismatch;
- uses argument-driven helper script: `skills/publish-repo/scripts/publish_repo.sh`;
- includes AgInTi compatibility notes in `references/aginti-compatibility.md`.

Assessment:

This is a good reusable release-engineering skill. Its helper script is conservative and should be safe for agent use when the user explicitly asks to publish.

### `video-face-image-replacement`

Purpose:

Cover or replace video faces with generated or supplied image assets, including animal/avatar masks and multi-person identity tracking.

Important design points:

- distinguishes non-human overlay replacement from human identity face-swap workflows;
- recommends InsightFace/SCRFD first, then RetinaFace, MediaPipe, and Haar fallback;
- preserves original source and audio;
- stores stable `identity_map.json`;
- includes keyframe RGB mask propagation guidance;
- explicitly warns against public gender inference claims.

Assessment:

This is an operationally useful media skill. It is careful about consent boundary and source preservation. It should remain a workflow skill, not a promise that every environment has the required face-detection stack installed.

### `transcript-video-section-splitter`

Purpose:

Transcribe video, derive natural topic boundaries, and split source or edited video into named clips with a manifest.

Important design points:

- transcribe first, do not cut by fixed duration alone;
- store section boundaries in JSON before cutting;
- use stream copy for fast keyframe cuts and re-encoding for frame-accurate cuts;
- supports reusing section JSON only when the edited variant preserves the same timeline.

Assessment:

This complements LazyEdit and media-report skills well. It correctly separates subjective boundary design from deterministic ffmpeg cutting.

### `aginti-agentlink`

Purpose:

Coordinate multiple agent sessions across machines, repos, tools, devices, and runtimes.

Important design points:

- defines agent nodes, agent links, peer maps, handoff packets, and action contracts;
- prioritizes live state and tracked docs over raw chat history;
- keeps raw session mirrors in ignored private folders;
- includes helper scripts for handoff template generation and JSONL session summarization.

Assessment:

This is a strong abstraction for multi-agent work. The core value is making collaboration explicit instead of relying on chat memory. It should stay protocol-oriented and avoid becoming a place for project-specific private logs.

### `kv260-metavision-lab`

Purpose:

Operate and maintain the AMD Kria KV260 + Prophesee Metavision lab.

Important design points:

- covers PetaLinux desktop launchers, custom event viewer, native `metavision_viewer`, recording API, Windows X11 control center, and file-transfer GUI;
- includes a mostly read-only probe script: `scripts/kv260_metavision_probe.sh`;
- records the `/dev/video0` ownership constraint;
- keeps raw recordings outside git.

Assessment:

This is useful but intentionally site-specific. It includes concrete paths such as `/home/petalinux/Projects/kria-kv260-starter` and should be labeled as a lab operational skill, not a generic embedded-vision skill.

### `kv260-windows-arduino`

Purpose:

Coordinate KV260 event recording with a Windows host and USB Arduino light controller.

Important design points:

- documents LAN identities and role split;
- uses KV260 as the recording device and Windows as Arduino USB controller;
- distinguishes the KV260 recording API on `8765` from the future Windows Arduino API on `8780`;
- includes scripts for lab status, one-shot recording, Windows Arduino probe, and Windows Codex session mirror fetching;
- explicitly says the Arduino has no IP address and should be controlled through Windows.

Assessment:

This is a high-context lab skill. It is valuable for continuity across Codex/AgInTi sessions, but contains hostnames, IPs, and path assumptions. That is acceptable because the skill is operational memory for this lab. It should not be generalized without parameterizing those values.

### `lazyedit-publish-workflow` Expansion

New material includes:

- default logo burn rule for real publishes;
- logo state check via LazyEdit UI settings endpoint;
- subtitle correction "human middle path" guidance;
- duplicate Whisper/transcription DB recovery notes;
- direct local section clip publishing workflow;
- guidance for context prompt wrappers and cleanup.

Assessment:

The additions reflect real operational failures and recovery paths. They are useful but now make the skill longer and more project-specific. If this keeps growing, split deep recovery recipes into `references/` and keep `SKILL.md` focused on the common path.

## Current Repository Shape

Top-level platform files:

```text
AGENTS.md
CLAUDE.md
GEMINI.md
.github/copilot-instructions.md
.github/instructions/lazyskills.instructions.md
skills.json
scripts/lazyskills.py
website/
docs/
i18n/
skills/
```

The repo remains platform-neutral in structure. Skills are canonical under `skills/<id>/SKILL.md`, with optional `scripts/`, `references/`, and `agents/`.

## Validation Performed

Commands executed:

```bash
git status --short --branch
git pull --ff-only
git log --oneline c0e2832..HEAD
git diff --stat c0e2832..HEAD
git diff --name-status c0e2832..HEAD
python3 scripts/lazyskills.py validate
python3 scripts/lazyskills.py list --json
bash -n skills/publish-repo/scripts/publish_repo.sh
bash -n skills/kv260-metavision-lab/scripts/kv260_metavision_probe.sh
bash -n skills/kv260-windows-arduino/scripts/fetch-windows-codex-session.sh
bash -n skills/kv260-windows-arduino/scripts/kv260-lab-status.sh
bash -n skills/kv260-windows-arduino/scripts/kv260-record-once.sh
bash -n skills/kv260-windows-arduino/scripts/windows-arduino-probe.sh
python3 -m py_compile skills/aginti-agentlink/scripts/agentlink_handoff.py skills/aginti-agentlink/scripts/agentlink_jsonl_summary.py
gh run list --repo lachlanchen/LazySkills --workflow pages.yml --limit 5
curl -fsS https://lachlanchen.github.io/LazySkills/
curl -fsS https://lachlanchen.github.io/LazySkills/skills.json
```

Results:

- repo pull succeeded;
- worktree clean after pull;
- `scripts/lazyskills.py validate` passed;
- shell helper syntax checks passed;
- AgentLink Python helper syntax checks passed;
- GitHub Pages workflow runs are succeeding after the website setup;
- live `skills.json` endpoint returns 12 skills.

## Main Finding

The website is stale relative to the catalog.

Observed live site:

```text
hero skill count: 7
listed skill cards:
- LALACHAN Xiaoyunque browser video
- LazyEdit publish workflow
- Media transcription report
- NPM publishing
- Publish repo
- OCR book polisher
- PocketPolyglot bookmaker
```

Observed live `skills.json`:

```text
12 skills
```

Missing from website skill cards:

```text
video-face-image-replacement
transcript-video-section-splitter
aginti-agentlink
kv260-metavision-lab
kv260-windows-arduino
```

Recommendation:

Change the website to render skill cards from `skills.json`, or update `website/index.html` whenever `skills.json` changes. Rendering from `skills.json` is preferable because the GitHub Pages workflow already copies `skills.json` into the deployed artifact.

## Risk Notes

### Site-specific skills

`kv260-metavision-lab` and `kv260-windows-arduino` encode real lab paths, hostnames, IPs, and service ports. This is useful as operational memory but should stay clearly scoped.

Do not present these as generic hardware control skills without adding parameterized host/project configuration.

### LazyEdit skill growth

`lazyedit-publish-workflow/SKILL.md` is accumulating recovery procedures. The skill still works as a practical playbook, but continued growth may make it expensive for agents to load.

Recommendation:

- keep the common publish path in `SKILL.md`;
- move detailed DB recovery, logo verification, section-clip publishing, and special cases into `references/`;
- keep trigger and acceptance criteria concise.

### Website maintenance

The website currently has manual skill cards. This caused drift within a day of initial launch.

Recommendation:

- add a tiny `website/site.js` that fetches `skills.json` and renders cards;
- keep static fallback cards only for no-JS or fetch failure;
- keep the hero count dynamic.

## Overall Assessment

LazySkills has matured from a small creative/publishing skill pack into a broader portable agent-skill library.

Current strengths:

- clear platform-neutral structure;
- `skills.json` as a real machine-readable catalog;
- strong validation discipline;
- deterministic helper scripts for fragile workflows;
- useful separation between skills, references, scripts, and platform entrypoints;
- growing coverage across publishing, media, release engineering, books, multi-agent coordination, and lab hardware.

Current priority fix:

Keep the website synchronized with `skills.json`.

Suggested next task:

Update the website to render all 12 skills from `skills.json`, then rerun Pages deployment and verify the live page count matches the live catalog.
