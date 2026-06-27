---
name: musai-song-localization
description: Use when working on Musai, AI song localization, song-to-Chinese or cross-language re-singing, extracting bass/drums/vocals/other stems, lyrics, beats, chords, phrase timing, singable lyric adaptation, YingMusic-Singer-Plus or SoulX-Singer synthesis preparation, or creating same-music translated singing artifacts.
---

# Musai Song Localization

## Purpose

Use this skill for Musai-style music localization: keep the song arrangement, rhythm, beats, chords, and melody, while adapting lyrics into another language and preparing singing synthesis artifacts.

## Non-Negotiables

- Do not present speech TTS as the final result for a singing localization request.
- Preserve the original music path whenever possible: `bass`, `drums`, `other` form `instrumental`; `vocals` or `human_sound` provide melody/timbre reference.
- Treat the four Demucs stems as `bass`, `drums`, `vocals`, and `other`.
- For Chinese output, adapt for singability: phrase duration, syllable/character count, rhyme, natural Chinese, emotional meaning, and tone-melody comfort.
- If singing model weights are not installed, produce a complete localization package and clearly mark vocal synthesis as blocked, not completed.
- Avoid cloning or imitating a real singer unless the user owns or has consent for that voice.

## Local Musai Repo Workflow

Default repo path:

```text
/home/lachlan/ProjectsLFS/Musai
```

Run local analysis:

```bash
PYTHONNOUSERSITE=1 conda run -n musai python scripts/run_pipeline.py INPUT_AUDIO \
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
python /home/lachlan/.codex/skills/musai-song-localization/scripts/create_localization_pack.py \
  --run-dir /home/lachlan/ProjectsLFS/Musai/data/runs/RUN_NAME \
  --target-language zh-CN \
  --target-lines TARGET_LINES.txt \
  --output-dir /home/lachlan/ProjectsLFS/Musai/data/runs/RUN_NAME/localization/zh-CN
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

The Musai repo contains helper scripts for large optional backends. Keep weights, envs, and caches local and ignored by git:

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

## References

- Read `references/workflow.md` for the detailed workflow, quality gates, and failure modes.
