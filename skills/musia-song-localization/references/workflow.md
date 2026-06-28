# Musia Song Localization Workflow

## Quality Target

A real localized song keeps:

- same arrangement
- same beat grid
- same chord movement
- same melody contour
- same phrase entrances and exits
- natural target-language lyric
- singable syllable density
- target-language prosody
- legal voice/rights posture

## Local Analysis Steps

1. Confirm the user has rights or is using public-domain/open/owned material.
2. Run Musia pipeline to produce stems, lyrics, beats, chords, and manifest.
3. Use `stems/vocals.wav` for ASR and melody reference.
4. Use `stems/instrumental.wav` for chord/beat analysis and final mix.
5. Use `analysis/lyrics.json` word/segment timings when reliable; otherwise use user reference lyrics.
6. Treat planned lyrics as correction evidence. Final published timing must follow the actual audible vocal.

## Chinese Adaptation Heuristics

For each phrase:

- Match phrase duration.
- Keep Chinese characters close to the source sung syllable count.
- Prefer natural Mandarin over literal translation.
- Keep emotional image and dramatic function.
- Keep strong vowels on long notes where possible.
- Avoid dense consonant clusters in fast note runs.
- Avoid awkward tone clashes on obvious rising/falling sustained notes when alternatives exist.
- Use line endings that can rhyme or assonate naturally.

Example target-line scoring dimensions:

```text
meaning: 0-5
singability: 0-5
duration fit: 0-5
character/syllable fit: 0-5
tone-melody comfort: 0-5
poetic Chinese: 0-5
```

## Output States

Use these names consistently:

- `analysis_complete`: stems/lyrics/beats/chords are available.
- `localized_lyrics_complete`: target-language lyrics and synthesis request are ready.
- `vocal_synthesis_blocked`: no usable singing backend/weights yet.
- `localized_vocal_complete`: target-language sung vocal exists.
- `final_mix_complete`: localized vocal is mixed with original instrumental.

## Website Lyric Sets

Use shared website `textTracks[]` only when all playable vocals share the same line structure and timing.

Use per-vocal `lyricSets[]` when English, Chinese, Japanese, or other vocals are independent renders or imperfect localizations. Each vocal gets its own trilingual group:

```text
en-vocal: en + zh-Hans + ja tracks based on the English vocal
zh-vocal: zh-Hans + en + ja tracks based on the Mandarin vocal
ja-vocal: ja + zh-Hans + en tracks based on the Japanese vocal
```

The active vocal language owns timing and word highlighting. Other tracks in that set are translations of the active vocal's real sung lines. If a line is missing, repeated, or changed in the audio, reflect the audio.

## Backend Notes

YingMusic-Singer-Plus is the best fit for same-melody lyric editing because it is designed for lyric manipulation with melody preservation. It needs its own environment and model weights. Do not install it into the lightweight `musia` analysis env unless the user explicitly accepts dependency churn; prefer a separate `yingmusic` conda env.

SoulX-Singer is strong for zero-shot singing and F0/MIDI conditioning, but custom-song synthesis requires metadata and sometimes manual alignment correction.

RVC/GPT-SoVITS can help with timbre but does not solve lyric adaptation or singing creation by itself.

## Reporting

Always tell the user:

- which song was used
- where the output folder is
- which artifacts are complete
- whether the Chinese sung vocal exists or synthesis is still blocked
- which exact command would complete synthesis once weights/backend are ready
- whether website lyrics are shared `textTracks[]` or per-vocal `lyricSets[]`
