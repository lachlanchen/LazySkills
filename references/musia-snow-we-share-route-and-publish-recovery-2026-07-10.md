# Musia Snow We Share Route And Publish Recovery - 2026-07-10

This note records the durable lessons from correcting and publishing
`共白头 · Snow We Share · 雪中回声`.

## Successful Route

The old public Snow We Share route is a successful sparse mixed-language hook
route. It used pinyin/romaji as private pronunciation control, kept the hook
short, and produced a usable emotional vocal. Do not discard this route because
a later native-character remake sounded worse. If the user praises the old
version, treat the old sparse route as the baseline.

Nearby successful Musia references:

- `越人歌`: source-line selection/repetition, focused ancient-song prompt,
  public restoration when ASR guessed nearby but less beautiful words.
- `共饮长江水`: sparse English-led mixed phonetic lyric, then public lyrics
  corrected from actual audio.
- `哭晁卿衡`: mixed EN/JA/ZH song where poem lines stayed as poem lines and
  non-Chinese lines were corrected from ASR plus listening, not translated from
  the poem.
- `共白头 · Snow We Share · 雪中回声`: sparse hook route with soft English
  continuation and final Chinese tail recovered by no-VAD/manual listening.

Musia repo reference:

`/home/lachlan/ProjectsLFS/Musia/references/musia-successful-song-routes-2026-07-10.md`

## Lyric Correction Lesson

The corrected public Snow We Share lyric needed a second pass because normal
segment ASR missed soft sung material. A no-VAD cross-check on the vocal stem
recovered the missing continuation:

```text
50.67-56.13 Let our hearts be less alone
56.13-63.73 Ah ah ah ah ah ah
64.36-67.00 Onaji yuki no shita de
67.00-70.42 Shiroku nareru kana
70.42-73.58 Ta zhao ruo shi tong lin xue
74.42-78.12 Ye suan gong bai tou
```

When a gap follows a hook, do not assume it is instrumental until the separated
vocal, no-VAD ASR, waveform energy, and focused listening all support that. Add
soft sung phrases when audible. Do not add musical-note lyric rows; instrumental
spans are UI state, not song lyrics.

Public correction rule:

```text
actual audible structure > close intended lyric > ASR guess > translation draft
```

Preserve the planned/source lyric when sound, phrase count, and meaning are
close and the source is more beautiful. Change it only when the sung structure
or sound is genuinely different.

## Direct HQ AutoPublish Recovery

For 4K Musia website recordings with small text, inspect the publish MP4 before
submitting. In this run, a LazyEdit logo-only processed output was much smaller
than the source recording and looked lower quality. The correct recovery was to
publish the inspected 4K recording directly with clean metadata.

Checklist:

1. Inspect source and processed MP4 with `ffprobe`.
2. Extract at least one sample frame and visually check text sharpness, logo,
   lyric layout, and chord/fingering layout.
3. If LazyEdit processing lowers quality, build a direct AutoPublish package
   from the approved MP4 instead of reprocessing.
4. Use a clean listener-facing metadata JSON. Do not reuse generated metadata
   that invents languages, wrong lyric phrases, or workflow notes.
5. Copy the direct ZIP to the remote AutoPublish `transcription_data/<stem>/`
   folder.
6. POST `/publish` with `filename=<zip-name>` and platform flags; do not use
   `path=...` for this endpoint.

Example direct package:

```bash
python scripts/lazyedit_direct_autopublish_package.py \
  --video /path/to/approved-4k-recording.mp4 \
  --cover /path/to/cover.jpg \
  --metadata-json /path/to/clean-metadata.json \
  --output-dir DATA/<stem>/publish \
  --stem <stem>
```

Example remote publish:

```bash
curl -fsS -X POST http://lazyingart:8081/publish \
  -d filename=<stem>.zip \
  -d publish_shipinhao=true \
  -d publish_y2b=true \
  -d publish_instagram=true \
  -d publish_douyin=true \
  -d reuse_existing=true
```

If the AutoPublish app is interrupted, the in-memory queue can be lost. Requeue
the same verified direct package. If one platform's browser is stale, restart
only that platform with `restart_platforms=shipinhao,youtube,instagram,douyin`
as needed, using the same ZIP.
