---
name: musia-lalachan-mv-workflow
description: Use when creating a music-video handoff from a reviewed Musia song to LALACHAN/Xiaoyunque, including full-song MV planning, chorus or climax MV cuts, uploaded asset prompts, song-locked audio replacement, and LazyEdit-ready outputs.
---

# Musia To LALACHAN MV Workflow

Use this skill when a song should become a LALACHAN-style MV with characters, story, Xiaoyunque generation, and final audio controlled by the Musia master track.

## Core Rule

The song is the timing authority. Generate or edit video to fit the reviewed Musia audio, not the other way around. If the video tool changes the music, export a song-locked final by muxing the generated visuals with the Musia master audio.

Use portable environment variables in docs and examples:

```bash
export MUSIA_ROOT="${MUSIA_ROOT:-/path/to/Musia}"
export LALACHAN_ROOT="${LALACHAN_ROOT:-/path/to/LALACHAN}"
export LAZYSKILLS_ROOT="${LAZYSKILLS_ROOT:-/path/to/LazySkills}"
```

## Choose The MV Type

**Full-song MV**: choose when the user wants a complete MV, when the song is 45s or longer, or when the concept needs setup, conflict, climax, and resolution.

**Chorus / climax MV**: choose when the user wants a short social cut, has limited credits, asks for 副歌/高潮部分, or wants to test the strongest hook before generating a long version.

For deeper mode selection, read:

```text
references/full-vs-chorus-mv.md
```

## Full-Song Workflow

1. Confirm the reviewed audio path, duration, language, and emotional arc.
2. Write a simple story with a beginning, tension, musical climax, and ending.
3. Create timestamped segments that follow the song sections.
4. Write a Xiaoyunque prompt that references uploads as `图1`, `图2`, `音频1`, never local paths.
5. Keep dialogue short and place it in musical gaps.
6. For character MVs, explicitly state that the characters can perform the song: one lead-singer character, short chorus echo, clapping, dancing, or rally shouts. Keep music primary.
7. If the generated storyboard duration drifts away from the song duration, correct it before paid render.
8. Generate the video, download it, and verify duration/audio with `ffprobe`.
9. If needed, mux the Musia master audio back in.
10. Publish through normal LazyEdit logic only when public posting is requested.

## Chorus / Climax Workflow

1. Locate the strongest 10-30s hook with listening, waveform, lyrics, or analysis artifacts.
2. Trim the hook with light fades.
3. Write one visual idea only: charge, dance, transformation, joke, or emotional payoff.
4. Generate a short MV with fewer story beats and less dialogue.
5. Make the ending loopable or suitable as a trailer for the full MV.

Example trim:

```bash
ffmpeg -y -ss START_SECONDS -i "$MUSIA_ROOT/data/creative_projects/SONG/final/selected.mp3" \
  -t 15 \
  -af "afade=t=in:st=0:d=0.2,afade=t=out:st=14.4:d=0.6,loudnorm=I=-16:TP=-1.5:LRA=11" \
  -c:a libmp3lame -b:a 192k hook-15s.mp3
```

## Prompt Rules

The generation prompt should include:

- clean asset labels such as `图1`, `图2`, `音频1`;
- music timing and mood;
- scene order;
- short dialogue and SFX guidance;
- character performance language when needed, e.g. `阿芽酱是主唱感，其他伙伴在副歌处轻轻跟唱、合唱或回应`;
- explicit no-subtitle/no-path instruction.

The prompt should not include:

- personal filesystem paths;
- long hidden production notes;
- full lyrics as visible text;
- dense dialogue over vocals;
- LazyEdit packaging instructions.

## Xiaoyunque Browser Download Fallback

Sometimes the generic DOM watcher does not see a normal `<video>` URL even when the Agent thread is complete. In that case:

1. Open the right-side resource panel.
2. Find `视频 -> 生成结果 -> final_video.mp4`.
3. Click `final_video.mp4`.
4. Click the preview-panel `下载` button.
5. Wait for the button to progress from `下载中 NN%` to a completed file in the browser downloads folder.

Use a filesystem wait helper or equivalent shell loop to avoid copying a partial download:

```bash
start="$(date +%s)"
# click the Xiaoyunque preview download button here
wait_downloaded_mp4.sh --since-epoch "$start" --min-bytes 1000000 --timeout 300
```

## Final Audio Helper

Use the bundled helper when the video looks good but the audio was changed:

```bash
$LAZYSKILLS_ROOT/skills/musia-lalachan-mv-workflow/scripts/mux_musia_audio.sh \
  --video GENERATED_VISUAL.mp4 \
  --audio SELECTED_MUSIA_MASTER.mp3 \
  --output FINAL_SONG_LOCKED.mp4
```

## Publish Rule

For public publishing, use the normal LazyEdit publish workflow. Do not manually burn subtitles or logos unless the user explicitly asks for a recovery/custom-master path. Metadata should be concise and viewer-facing, not a storyboard dump.

For LALACHAN character MVs, set `publish_category: lalamv`; target YouTube playlist `LalaMV` and Shipinhao collection `LalaMV` when available. Use LazyEdit's built-in portrait blur-fill and normal subtitle/logo reburn for mobile versions; current MV logo default is top-right. If a platform category UI is unstable or missing, publish should continue and report the category limitation instead of wasting a completed render.
