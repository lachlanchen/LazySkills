---
name: transcript-video-section-splitter
description: Use when transcribing a video, deriving topic-based section boundaries from the transcript, and splitting the video into named clips with ffmpeg plus a manifest, instead of cutting by fixed duration.
triggers:
  - split video by transcript
  - split video into sections
  - transcript based video split
  - video chapters from transcription
  - content based video clips
  - Whisper video sections
  - split panda face video
  - generate section clips from transcript
---

# Transcript Video Section Splitter

Use this skill when the user wants a long video divided into meaningful content sections based on what is said. The output should include a timestamped transcript, section metadata, and split video clips.

## Core Rules

- Transcribe first; do not guess section boundaries from duration alone.
- Keep the original media unchanged. Split from a derived edited video when the user asks to section that edited version.
- Use topic changes, long pauses, repeated framing phrases, and concrete action shifts to set boundaries.
- Store section boundaries in durable JSON before cutting clips.
- Preserve audio and avoid unnecessary re-encoding when exact keyframe cuts are acceptable; re-encode when frame-accurate starts matter.
- Keep private or raw transcripts separate when the clips or section summaries will be published.

## Recommended Layout

```text
text/
  source.md                         # timestamped transcript
artifacts/video_sections/
  source_sections.json              # machine-readable boundaries
  source_sections.md                # human-readable chapter table
  clips/
    01_topic-slug.mp4
    manifest.json
```

## Transcription

Use the project convention first. Common commands:

```bash
python transcribe.py \
  -i video/source.mp4 \
  -o text/source.md \
  -m medium \
  -l zh
```

For higher-quality alignment or speaker labels:

```bash
conda run -n whisperx whisperx video/source.mp4 \
  --model large-v2 \
  --language zh \
  --task transcribe \
  --output_dir text/source.whisperx \
  --output_format json
```

## Section Metadata

Create JSON with explicit starts, ends, slugs, titles, and summaries:

```json
[
  {
    "index": 1,
    "start": "00:00:00.000",
    "end": "00:00:52.000",
    "slug": "problem-framing",
    "title": "Problem framing",
    "summary": "The opening defines the key problem and constraints."
  }
]
```

Boundary guidance:

- Use `00:00:00.000` for the first start unless there is a clear pre-roll to remove.
- End the final section at the media duration from `ffprobe`.
- Prefer section lengths that match natural content, not equal sizes.
- Avoid cutting in the middle of a sentence unless the user asks for short social clips.
- Include a Markdown table for review before cutting if the sectioning is subjective.

## Splitting

Stream-copy is fast but may cut on nearby keyframes:

```bash
ffmpeg -y -ss 12.000 -i edited_video.mp4 -t 48.000 -c copy clips/01_topic.mp4
```

Use re-encoding for frame-accurate cuts:

```bash
ffmpeg -y -ss 12.000 -i edited_video.mp4 -t 48.000 \
  -c:v libx264 -pix_fmt yuv420p -c:a aac clips/01_topic.mp4
```

Write a `manifest.json` with clip index, title, start, end, duration, and path.

## Validation Checklist

- Transcript exists and includes timestamps.
- Section JSON covers the full intended duration without overlap or gaps.
- Section titles and summaries are content-based and neutral.
- Clips exist, play, and preserve audio.
- Manifest matches the generated clip filenames.
- At least the first, middle, and final clips are spot-checked.
- Generated sections are derived from transcript content, not private chat context.
