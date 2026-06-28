---
name: musai-music-production
description: Use when generating, correcting, reviewing, documenting, publishing, or handing off original music in Musai, including idea-to-song, lyrics-to-song, melody/chord-controlled songs, ACE-Step/YuE/SoulX route selection, vocal quality checks, song review reports, Fun Lazying Art website publishing, per-vocal lyric sets, and LALACHAN song-first video handoffs.
---

# Musai Music Production

Use this skill for original song creation and review. For strict same-song localization, also use `musai-song-localization`.

## Default Repo

```text
/home/lachlan/ProjectsLFS/Musai
```

## Core Rule

Do not accept a generated song just because a WAV exists. A usable song needs:

- audible sung vocal;
- healthy levels;
- coherent tempo/chord analysis;
- saved lyrics and prompt;
- review report;
- human listening pass when the result matters.

Planned lyrics are intent, not truth. After generation, use listening and ASR/STT evidence to decide what the render actually sang. If the rendered vocal differs from the planned lyric, document the mismatch and publish lyrics/timing that match the audio.

Avoid real singer imitation or voice cloning unless the user owns or has explicit consent.

## Beautiful Song Standard

Before generating, write a compact producer brief with:

- emotional arc;
- short singable lyric lines;
- duration, language, key/BPM when known;
- arrangement and vocal direction;
- negative instructions such as no clipped endings, no buried vocal, and no real-singer imitation.

Prefer fewer stronger lines over dense poetry. For Chinese/Japanese, reduce pronunciation risk by using natural, short phrases and correcting after ASR/listening.

## Fast Workflow

Create a song package:

```bash
musai song init \
  --title "Song Title" \
  --idea "short concept" \
  --vocal-language ja \
  --lyrics-file lyrics.txt \
  --genre "cinematic J-pop" \
  --style "piano, warm strings, gentle drums" \
  --voice-notes "clear upfront young female vocal, no real singer imitation"
```

Generate:

```bash
data/creative_projects/<song-id>/commands.sh generate
```

Review:

```bash
data/creative_projects/<song-id>/commands.sh review
```

If the review shows quiet vocals, wrong language, clipped endings, or poor lyric recovery, do not publish as final. Run a correction pass or label it as experimental.

Correct:

```bash
musai song correct \
  --project-dir data/creative_projects/<song-id> \
  --issues "vocal unclear or endings clipped" \
  --caption-extra "clearer vocal, fewer words per line" \
  --lyrics-file corrected-lyrics.txt
```

Handoff to LALACHAN:

```bash
musai song handoff \
  --project-dir data/creative_projects/<song-id> \
  --audio data/creative_projects/<song-id>/final/selected.mp3 \
  --cover data/creative_projects/<song-id>/assets/cover-16x9.png
```

## Reusable Script

Primary script:

```text
scripts/musai_song_workbench.py
```

It supports:

```text
init
review
correct
handoff
find-audio
```

Generated song folders are intentionally ignored by git:

```text
data/creative_projects/<song-id>/
```

## Model Routing

- Idea/lyrics to full song: ACE-Step 1.5 first.
- Vocal-only controlled short hook: SoulX if language metadata is supported.
- Strict source-song localization: Demucs/analysis plus YingMusic/SoulX prep, not full-song generation.
- If Japanese/Chinese lyric accuracy is poor: shorten lines, reduce kanji ambiguity, increase vocal clarity in caption, try new seed/model, or use a specialized vocal workflow.

## Website Publishing Rule

For `fun.lazying.art`, use shared `textTracks[]` only when all playable vocals truly sing the same line structure. If English, Chinese, and Japanese renders are independent or imperfect, create per-vocal `lyricSets[]`:

```text
lyrics/en-vocal/en.json
lyrics/en-vocal/zh-Hans.json
lyrics/en-vocal/ja.json
lyrics/zh-vocal/en.json
lyrics/zh-vocal/zh-Hans.json
lyrics/zh-vocal/ja.json
lyrics/ja-vocal/en.json
lyrics/ja-vocal/zh-Hans.json
lyrics/ja-vocal/ja.json
```

The active vocal owns timing and word highlighting. Other languages in the same set are translations of that vocal's actual sung lines.

## References

Read only as needed:

```text
references/musai-song-generation-and-website-runbook.md
references/musai-song-workbench.md
references/lalachan-song-first-video-workflow.md
references/musai-full-capability-guide.md
references/musai-creative-studio.md
references/musai-website-json-format.md
```
