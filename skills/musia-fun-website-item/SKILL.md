---
name: musia-fun-website-item
description: Use when preparing, auditing, fixing, documenting, or publishing a Fun Lazying Art website media item for Musia, including ASR/STT-corrected lyrics, multilingual lyric JSON, per-vocal lyric sets, timing and word highlighting, pinyin/furigana/Jyutping ruby, 16:9 covers, manifests, website validation, and player recording.
---

# Musia Fun Website Item

Use this skill after a song, localization, MV, short film, or vocal render has been selected for `fun.lazying.art`. This skill is about truthful website publication, not about accepting raw generation quality.

## Default Repo

```text
/home/lachlan/ProjectsLFS/Musia
```

## Core Rule

The website must match the real audio. Planned lyrics, prompts, and translations are references; ASR/STT, listening, and phrase timing are evidence. If a vocal repeats, skips, garbles, or changes a line, the published lyric set must reflect that vocal or the vocal should stay experimental.

For generated multilingual songs, treat each playable vocal as its own evidence
source. A Chinese, English, Japanese, Cantonese, or mixed render may diverge
from the prompt and from the other language renders, even when they came from
the same master package. Do not copy another vocal's lyric text, timing, or
translations into a public lyric set unless ASR/listening proves that exact
audio actually sings the same structure.

The prompt lyric is only a reference until the selected audio confirms it. If a
vocal is unclear, garbled, skips words, repeats a line, or sings different text:

- correct the active lyric track to the audible line;
- mark that vocal experimental and keep it out of public/recorded outputs; or
- regenerate before publication.

Do not prettify translations into lyrics the audio did not sing.

For every selected Musia song that is not explicitly private or experimental,
website preparation is part of the definition of done. Always prepare the data
for `fun.lazying.art` after song creation:

```text
selected audio -> ../MusiaSongs/audio/*.mp3
../MusiaSongs/audio.json
website/data/songs/<media-id>/manifest.json
website/data/songs/<media-id>/lyrics/<vocal-set>/<lang>.json
website/assets/covers/<media-id>-16x9.png
website/data/catalog.json
```

Then validate both repos before final response.

When the song will also be published through LazyEdit/Shipinhao Music, the
music package must reuse the corrected website lyric JSON for the selected
vocal. Pass that exact active-language file as `--lyrics-json`; never hand off
the original prompt lyric, draft lyric, or another vocal's lyric set as the
music-platform lyric source.

Do not let ASR override a good intended lyric just because the recognizer chose
a nearby word. If the input/reference lyric is phonetically close, fits the
sentence better, and the phrase structure has not changed, preserve the input
lyric. Use ASR to catch real omissions, repeats, order changes, and garbling,
not to downgrade plausible words such as `When` into `In` when listening and
context support `When`.

## Workflow

1. Run or collect analysis for every public vocal:

```bash
PYTHONNOUSERSITE=1 conda run -n musia python scripts/run_pipeline.py AUDIO \
  --run-name <media-id>-<vocal>-analysis \
  --max-duration 180 \
  --asr-model small \
  --language LANG
```

2. Correct lyrics using at least two sources:

- ASR/STT from that same selected vocal or stem, not only the master render or
  planned lyric;
- input/reference lyric, second ASR, or manual listening;
- phrase timing, separated vocal, and repeated listening when they disagree.

Use this evidence policy:

```text
actual audible structure > close intended lyric > ASR guess > translation draft
```

For close word-level conflicts, prefer the input/reference lyric when it is
sound-close and grammatically/musically stronger. Override it only when ASR plus
listening show a real structural change: missing line, repeated line, changed
line order, different phrase length, or a clearly different word.

Normalize model-facing language codes before ASR/model calls: use `zh` for
Mandarin when the website track is `zh-Hans` / `zh-Hant`, and use `yue` for
Cantonese when the website track is `yue-Hant` / `yue-Hans`. Keep the public
website JSON code as `zh-Hans`, `zh-Hant`, or `yue-Hant`.

3. Choose the JSON shape:

- shared `textTracks[]` only when all playable vocals truly share line IDs and timing;
- per-vocal `lyricSets[]` when vocals are independent, imperfect, translated, mixed-language, or have different timing.

4. Build lyric tracks:

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
lyrics/mixed-vocal/mul.json
lyrics/yue-vocal/yue-Hant.json
```

Inside one lyric set, every track shares the same `line.id` sequence. The active vocal-language track owns line timing and exact word highlighting. Other tracks translate that active vocal's actual sung lines and may rough-highlight tokens inside the same current line.

5. Add pronunciation metadata:

- Mandarin CJK tokens: `pinyin`, such as `{"text": "光", "pinyin": "guang1"}`;
- Japanese kanji tokens: `reading`, such as `{"text": "光", "reading": "ひかり"}`;
- Cantonese CJK tokens: Jyutping in `reading`, such as `{"text": "光", "reading": "gwong1"}`.

Do not duplicate ruby by also putting pronunciation into the visible native text unless the active sung source is intentionally phonetic.

6. Prepare cover/poster:

- use 16:9 by default;
- save to `website/assets/covers/<media-id>-16x9.png`;
- set `assets.cover`, `assets.poster`, and `share.image`;
- record the cover prompt/source in `manifest.provenance` or the song production note.

7. Validate and audit:

```bash
npm run website:validate
musia fun-audit --media-id <media-id>
node --check website/app.js
git diff --check
```

Use strict audit mode before public release when reasonable:

```bash
musia fun-audit --media-id <media-id> --strict
```

The audit checks visible lyric script. Treat a warning such as Japanese or
Chinese visible text having high Latin content as a blocker unless the active
vocal is intentionally mixed-language and documented as mixed-language. Do not
leave English hooks in `ja.json`, `zh-Hans.json`, or `yue-Hant.json` just
because they came from a planning lyric; translate them or mark the active track
as mixed-language when the audio truly sings them.

8. Preview and record:

```bash
python3 -m http.server 9174 --directory website
musia fun-record --media-id <media-id> --skip-intro
```

When a Fun player recording is created, always sync the final MP4 to the
Nutstore Musia share folder before reporting completion:

```bash
mkdir -p "/home/lachlan/Nutstore Files/Projects/Musia"
cp -f RECORDED_VIDEO.mp4 "/home/lachlan/Nutstore Files/Projects/Musia/"
```

For multi-vocal recordings, render and sync one MP4 per public vocal/language,
and make sure `--asset-id` matches both the visible website player and the
muxed audio track.

## Quality Gate

Before calling an item public-demo quality:

- listen to every selected vocal;
- confirm every public vocal has an active-language lyric track corrected from
  its own ASR/STT/listening pass;
- confirm prompt-only lyrics were not used as public EN/JP/ZH/Cantonese lyrics
  unless the exact selected vocal was verified;
- confirm each vocal has its own lyric set unless ASR proves shared timing is correct;
- confirm the first highlighted line begins at the real vocal entrance;
- confirm active-vocal word highlighting does not jump into another language's future line;
- confirm translation highlighting stays within the current line ID;
- confirm the visible text language matches the track code, especially for
  Japanese/Chinese/Cantonese tracks;
- confirm close ASR substitutions were corrected against the intended lyric
  when pronunciation and context support the intended word;
- confirm pinyin/furigana/Jyutping display once and cleanly;
- confirm the chord row has a current highlighted chord when chord data exists;
- confirm title, artist `Musia`, cover, social image, and localized titles are present;
- if publishing to LazyEdit/Shipinhao Music, confirm the package uses the same
  corrected active-vocal lyric JSON as the website;
- confirm every requested recording has a Nutstore copy under
  `/home/lachlan/Nutstore Files/Projects/Musia/`;
- document ASR correction decisions and caveats under `references/`.

## Detailed Reference

Read only when preparing or reviewing a real website item:

```text
references/fun-website-item-preparation.md
references/musia-website-json-format.md
references/musia-song-generation-and-website-runbook.md
```
