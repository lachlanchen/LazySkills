---
name: musia-song-localization
description: Use when working on Musia, AI song localization, song-to-Chinese or cross-language re-singing, extracting bass/drums/vocals/other stems, lyrics, beats, chords, phrase timing, singable lyric adaptation, YingMusic-Singer-Plus or SoulX-Singer synthesis preparation, creating same-music translated singing artifacts, or fixing Fun Lazying Art per-vocal lyric/timing JSON.
---

# Musia Song Localization

## Purpose

Use this skill for Musia-style music localization: keep the song arrangement, rhythm, beats, chords, and melody, while adapting lyrics into another language and preparing singing synthesis artifacts.

## Non-Negotiables

- Do not present speech TTS as the final result for a singing localization request.
- Preserve the original music path whenever possible: `bass`, `drums`, `other` form `instrumental`; `vocals` or `human_sound` provide melody/timbre reference.
- Treat the four Demucs stems as `bass`, `drums`, `vocals`, and `other`.
- For Chinese output, adapt for singability: phrase duration, syllable/character count, rhyme, natural Chinese, emotional meaning, and tone-melody comfort.
- Same melody is not worth a bad song. If strict same-score localization makes the vocal unclear, robotic, badly pronounced, or musically weak, keep the artifact as experimental and regenerate a higher-quality independent version instead.
- If singing model weights are not installed, produce a complete localization package and clearly mark vocal synthesis as blocked, not completed.
- Avoid cloning or imitating a real singer unless the user owns or has consent for that voice.
- Do not reuse one vocal render's lyric timeline for another render unless listening/ASR confirms the renders truly match.
- Planned/reference lyrics are correction evidence, not the published truth. The published lyric timing must follow the actual audible vocal.

## Local Musia Repo Workflow

Default repo path:

```text
/home/lachlan/ProjectsLFS/Musia
```

Run local analysis:

```bash
PYTHONNOUSERSITE=1 conda run -n musia python scripts/run_pipeline.py INPUT_AUDIO \
  --run-name RUN_NAME \
  --max-duration 120 \
  --asr-model base.en \
  --language en \
  --demucs-device cuda
```

Expected artifacts:

```text
data/runs/RUN_NAME/stems/bass.wav
data/runs/RUN_NAME/stems/drums.wav
data/runs/RUN_NAME/stems/vocals.wav
data/runs/RUN_NAME/stems/other.wav
data/runs/RUN_NAME/stems/instrumental.wav
data/runs/RUN_NAME/stems/human_sound.wav
data/runs/RUN_NAME/analysis/lyrics.json
data/runs/RUN_NAME/analysis/beats.csv
data/runs/RUN_NAME/analysis/chords.csv
data/runs/RUN_NAME/manifest.json
```

## Chinese Localization Package

For high-quality Chinese localization, create a package before synthesis:

```bash
python /home/lachlan/.codex/skills/musia-song-localization/scripts/create_localization_pack.py \
  --run-dir /home/lachlan/ProjectsLFS/Musia/data/runs/RUN_NAME \
  --target-language zh-CN \
  --target-lines TARGET_LINES.txt \
  --output-dir /home/lachlan/ProjectsLFS/Musia/data/runs/RUN_NAME/localization/zh-CN
```

The package should include:

- `target_lyrics.txt`
- `target_lyrics.json`
- `target_text_yingmusic.txt`
- `yingmusic_request.jsonl`
- `synthesis_status.md`

## Singing Backend Priority

1. **YingMusic-Singer-Plus**: preferred for lyric manipulation and same-melody Chinese/English editing. Use `vocals.wav` as melody reference and `target_text_yingmusic.txt` as target text.
2. **SoulX-Singer**: preferred when MIDI/F0 conditioning and zero-shot singing are ready.
3. **Full-song models** such as ACE-Step/YuE: only for inspiration/new-song modes, not strict same-music localization.

If using YingMusic-Singer-Plus, prepare:

```text
ref_audio = stems/vocals.wav or a consented timbre reference
melody_audio = stems/vocals.wav
ref_text = source phrase text if reliable
target_text = phrase1|phrase2|phrase3...
output = localized_vocal_zh-CN.wav
then mix localized_vocal_zh-CN.wav + stems/instrumental.wav
```

## Local Quality Backend Setup

The Musia repo contains helper scripts for large optional backends. Keep weights, envs, and caches local and ignored by git:

```bash
bash scripts/download_quality_backends.sh all
bash scripts/install_quality_envs.sh all
```

Validated local helpers:

```bash
bash scripts/run_soulx_env.sh .conda/soulxsinger/bin/python -c "import soulxsinger; print('soulx ok')"
bash scripts/run_moss_music_env.sh .conda/moss-music/bin/python -c "import torchcodec; print('torchcodec ok')"
```

When quality is poor, prioritize a short 20-40 second chorus/verse render through SoulX-Singer or a professional synth workflow before attempting a full song. Accept a render only if the vocal is clearly sung, audible, natural in the target language, and aligned to the original phrase rhythm.

## LLM Prosody And Rhyme Check

Before finalizing EN/JP/ZH target lyrics, run a lyric-quality review with the
best available LLM path: OpenAI, DeepSeek, or a strong Codex/GPT-5.5 xhigh
reasoning pass. Ask for a compact score and specific rewrites for:

- phrase rhythm and breath points against the melody/timing;
- rhyme / 押韵, including slant rhyme where exact rhyme sounds forced;
- English stress and singable end words;
- Mandarin natural wording, character count, rhyme group, and tone-melody comfort;
- Japanese mora flow, vowel endings, particles, and rhyme-like vowel echoes;
- meaning preservation and emotional force.

Do not let the LLM make the lyric verbose. Prefer short, concrete, singable lines
that a vocal model can pronounce clearly.

## Website Lyric Protocol

For `fun.lazying.art`, use per-vocal `lyricSets[]` when generated or localized vocals differ by language, phrase count, repeated lines, or timing:

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

Each playable audio asset must set `lyricSetId`. The active vocal language owns timing and exact current-word highlighting. Other languages in the same set translate that active vocal's real sung lines and may rough-highlight corresponding tokens inside the same current `line.id`. If the vocal misses, changes, or repeats a planned line, reflect that fact.

For mixed-language vocals, use one active sung/phonetic track plus translation tracks:

```text
lyrics/mixed-vocal/mul.json
lyrics/mixed-vocal/en.json
lyrics/mixed-vocal/zh-Hans.json
lyrics/mixed-vocal/ja.json
```

If a local model fails to sing native CJK script reliably in a mixed render, use pinyin/romaji for the sung input and display native Chinese/Japanese in translation tracks with pinyin/furigana. Document the compromise instead of claiming native-script singing.

Shared `textTracks[]` are acceptable only for strict same-timeline media.

For public Fun player videos, keep the website frame clean: two-line KTV lyric carousel, visible current-chord highlighting, native-language labels, and no bottom full-lyrics section in capture mode. Use:

```bash
musia fun-record --media-id <media-id> --skip-intro
```

## References

- Read `references/workflow.md` for the detailed localization workflow, quality gates, and failure modes.
- In the Musia repo, read `references/musia-song-generation-and-website-runbook.md` for song-generation and website publishing rules.
- In the Musia repo, read `references/musia-website-json-format.md` before editing website lyric JSON.
