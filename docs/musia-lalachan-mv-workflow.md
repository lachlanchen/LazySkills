# Musia To LALACHAN MV Workflow

This document explains how to turn a reviewed Musia song into a LALACHAN/Xiaoyunque music video.

## Two Output Styles

### Full-Song MV

Use for a complete music video. This is best when the song is long enough for a story and the user wants the whole emotional arc.

Typical plan:

1. Read the selected Musia song handoff, lyrics, duration, and analysis.
2. Write a story with beginning, tension, climax, and ending.
3. Build timestamped segments that match the song sections.
4. Write a Xiaoyunque prompt with uploaded references only as `图1`, `图2`, `音频1`.
5. Generate video, download it, verify duration and audio.
6. If the music was changed, mux the Musia master audio back in.
7. Publish through normal LazyEdit logic only when requested.

Use this for the **Aya Chan Hikari Ame** full MV.

### Chorus / Climax MV

Use for a short promotional cut, hook test, or low-credit generation.

Typical plan:

1. Find the strongest 副歌 or 高潮部分.
2. Trim a 10-30s audio excerpt with fades.
3. Use one strong visual idea only.
4. Generate a short MV with minimal dialogue.
5. Optionally publish as teaser or social cut.

This should not try to compress the whole full-song story. It should sell one memorable moment.

## Prompt Quality Rules

Good MV prompts:

- follow music timing;
- describe clear scenes and emotions;
- keep character dialogue short;
- use sound effects lightly;
- say `不要字幕，不要歌词字幕，不要文件名、路径、说明文字`;
- never paste local filesystem paths.

Bad MV prompts:

- include long hidden production notes;
- ask for continuous talking over vocals;
- expose every storyboard beat as metadata;
- ask Xiaoyunque to draw file names or paths;
- overpatch with too many repeated warnings.

## Audio Rule

The reviewed Musia file is the master. If Xiaoyunque changes the song, keep the generated video track and replace audio with `ffmpeg`.

The portable skill helper:

```bash
$LAZYSKILLS_ROOT/skills/musia-lalachan-mv-workflow/scripts/mux_musia_audio.sh \
  --video GENERATED_VISUAL.mp4 \
  --audio SELECTED_MUSIA_MASTER.mp3 \
  --output FINAL_SONG_LOCKED.mp4
```

## Normal Publish Rule

After final video preparation, use LazyEdit’s normal pipeline for subtitles, logo, metadata, packaging, and platform publish. Do not make a custom subtitle/logo burn path unless the user explicitly asks for it.

Metadata should be concise and viewer-facing. Use the MV story as context for subtitle correction and title/description tone, not as the description body.

## Validation

Before generation:

- correct MV type selected: full song or chorus cut;
- song audio exists and is reviewed;
- prompt has no local paths;
- required images are uploaded as files;
- duration and ratio fit the target;
- visible UI state is checked before paid submit.

After generation:

- `ffprobe` confirms video duration, codec, and audio stream;
- human check confirms the music is not damaged;
- song-locked output is created when needed;
- LazyEdit publish, if requested, reaches final `done` status on target platforms.

