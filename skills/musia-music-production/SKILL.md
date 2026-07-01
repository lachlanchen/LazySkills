---
name: musia-music-production
description: Use when generating, correcting, reviewing, documenting, publishing, or handing off original music in Musia, including idea-to-song, lyrics-to-song, melody/chord-controlled songs, ACE-Step/YuE/SoulX route selection, vocal quality checks, song review reports, Fun Lazying Art website publishing, per-vocal lyric sets, and LALACHAN song-first video handoffs.
---

# Musia Music Production

Use this skill for original song creation and review. For strict same-song localization, also use `musia-song-localization`.

## Default Repo

```text
/home/lachlan/ProjectsLFS/Musia
```

## Runtime Rule

Use the unified `musia` conda environment for Musia Python tools. Prefer the
repo CLI wrapper because it automatically routes through
`conda run -n musia python ...`:

```bash
node bin/musia.js doctor --json
node bin/musia.js song review --project-dir data/creative_projects/<song-id>
node bin/musia.js fun-validate
```

Only bypass this with `MUSIA_PYTHON` or `MUSIA_NO_CONDA=1` when the user
explicitly asks or a tool cannot run inside the shared environment.

## Core Rule

Do not accept a generated song just because a WAV exists. A usable song needs:

- audible sung vocal;
- healthy levels;
- coherent tempo/chord analysis;
- saved lyrics and prompt;
- review report;
- human listening pass when the result matters.

Quality comes before same-melody control. If a same-score/same-F0 route makes
the vocal, pronunciation, phrasing, or arrangement worse, label that render
experimental and leave it out of the public/final path. Regenerate with the
best full-song model instead, even if EN/JP/ZH end up as independent high-quality
versions rather than one perfectly shared melody.

Planned lyrics are intent, not blind truth. After generation, use listening and ASR/STT evidence to decide what the render actually sang. If the rendered vocal repeats, skips, reorders, or clearly changes a phrase, document the mismatch and publish lyrics/timing that match the audio. If ASR only substitutes a nearby word and the planned lyric is phonetically close, grammatically stronger, and supported by manual listening, keep the planned lyric; do not let ASR downgrade `When` to `In` or similar close words just because the recognizer guessed that token.

Before calling the lyric correction complete, run a missing-planned-phrase audit:
compare the planned/reference lyric against the corrected active-vocal lines and
look for prompt phrases that ASR omitted, merged into a long segment, or placed
inside a timing gap. Short repeated or soft CJK phrases can be swallowed by ASR
even when audible. If listening supports the intended phrase, add it back with
real timing and translations; if it is not audible, document that it was skipped.
When the user later identifies a missed phrase, patch the website lyric JSON,
manifest timeline, and references immediately, then push/deploy if the item is
already public.

For multilingual companion renders, run that correction independently for each
selected audio. A Japanese render needs Japanese ASR/listening evidence; an
English render needs English ASR/listening evidence; a Chinese render needs
Chinese ASR/listening evidence. Do not assume a companion vocal matches its
prompt just because the lyric file was used during generation. If the vocal
diverges, publish the actual sung lyric, mark the render experimental, or
regenerate it before website/recording use.

Avoid real singer imitation or voice cloning unless the user owns or has explicit consent.

## Beautiful Song Standard

Before generating, write a compact producer brief with:

- emotional arc;
- short singable lyric lines;
- duration, language, key/BPM when known;
- arrangement and vocal direction;
- negative instructions such as no clipped endings, no buried vocal, and no real-singer imitation.

When the user says quality matters or has time to wait, use the best practical
local route before accepting a faster route:

- inspect installed model checkpoints before generation;
- for ACE-Step 1.5, prefer `acestep-v15-xl-sft` at 50 steps for final-quality
  full-song candidates when it is installed and VRAM allows;
- use `acestep-v15-xl-turbo` for rapid iteration, fallback batches, or when SFT
  fails, but do not silently treat it as the highest-quality route;
- if a newer XL/XXL/XXXL or higher-quality model is available in the upstream
  project or community and can be installed legally, download/test it before
  final publication when the user asks for best quality;
- keep the older model output only if listening and ASR prove it is better for
  the specific song;
- document the exact model, checkpoint, seeds, duration, and fallback reason in
  the project note.

Prefer fewer stronger lines over dense poetry. For Chinese/Japanese, reduce pronunciation risk by using natural, short phrases and correcting after ASR/listening.

For classical Chinese poems, especially Li Bai/Tang poetry, run a
pronunciation-prep gate before ACE/YuE generation:

- verify the source text and likely poem variant from at least one external
  source or local reference;
- search/check a poem-specific pinyin or annotated reading source when
  available;
- run pypinyin as a baseline, then manually audit polyphonic and rare
  characters such as `行`, `将`, `了`, names, place names, and classical words;
- write a pinyin guide and list risky pronunciations in the project notes;
- prefer an adapted modern-singable lyric when exact classical diction causes
  ACE to garble pronunciation, but preserve the poem's core images and
  document any omissions;
- add ACE-facing caption guidance for the risky words, and after generation
  compare ASR/listening against the pinyin guide before publishing.

For very short classical poems, do not assume a single exact pass is enough.
If ACE produces no ASR recovery, weak vocal text, or subtitle/credit leakage:

- repeat only original poem lines into a verse/chorus/hook form rather than
  adding modern words;
- emphasize the most important couplet or hook by repeating it;
- keep captions positive and compact, avoiding long forbidden-word lists that
  the model may sing;
- use private phonetic substitutions for rare characters, then restore the
  public original text only where sound-close;
- select by actual hook recovery and listening, not by model size alone.

For future original-poem experiments, create a recursive refinement package
instead of hand-building the project from scratch:

```bash
PYTHONNOUSERSITE=1 conda run -n musia python scripts/prepare_ace_poem_refinement_pack.py \
  --title "Poem Title" \
  --poem-file poem.txt \
  --hook "main emotional couplet" \
  --substitution "rare=common-sound-control"
```

Use the generated `REFINEMENT_PLAN.md`, `source/pronunciation-guide.md`,
repeated-hook lyrics, SFT/Turbo configs, and `commands.sh`. The successful
`越人歌 · 原诗版` route came from this philosophy: source truth -> pronunciation
truth -> private model-facing simplification -> multiple lyric layouts -> model
sweep -> ASR/listening rejection -> hook-focused regeneration -> truthful
website correction. Keep these references close when repeating the method:

```text
/home/lachlan/ProjectsLFS/Musia/references/ace-poem-song-beauty-and-lyric-alignment-method-2026-07-01.md
/home/lachlan/ProjectsLFS/Musia/references/yue-ren-ge-recursive-refinement-playbook-2026-07-01.md
```

When the user's quality goal is a beautiful song rather than a literal poetry
recitation, prefer a rewritten/adapted singable lyric route like the successful
`侠客行` workflow. Do not force the full original poem into ACE unless the user
explicitly asks for original-text-only output. Label full-original-poem renders
as `ACE Poetry Demo` or experimental when ASR shows garbling. For the adapted
route, preserve the poem's spirit, iconic images, and key lines, but rewrite
into short breath-friendly verse/pre-chorus/chorus/bridge sections before
generation.

Do not cram words into the song just to preserve every detail. Use musical
space: 留白, held vowels, rests, repeated hooks, and breath-friendly pauses.
Some lines should be sparse and some can be fuller; the goal is a proper fit
to the melody and emotion, not the fewest words and not the most words.

Do not overcorrect into lyrics that are too sparse. For ACE-style 80-95 second
short songs, prior successful Musia renders usually use a complete verse /
pre-chorus / chorus / bridge-or-outro shape with many short lines: roughly
30-45 CJK lines, average 4-7 CJK characters per line, and about 150-280 total
CJK lyric characters. Use this as a density target, then simplify only when
ASR/listening shows the model is skipping or garbling lines.

Before generating or accepting EN/JP/ZH lyrics, do an LLM lyric-quality pass
when an API/model is available. Use OpenAI, DeepSeek, or a strong Codex/GPT-5.5
reasoning pass to check:

- rhythm fit: short singable phrases, line length, phrase stress, and likely breath points;
- musical space / 留白: whether a line should hold notes, leave rests, or repeat a simple hook instead of adding more words;
- rhyme / 押韵: English end rhyme or slant rhyme, Chinese rhyme groups, Japanese vowel/mora echoes;
- language-specific fit: English stress, Chinese tone comfort and natural wording, Japanese mora flow and particles;
- emotional clarity: the lyric should say something concrete and singable, not just be poetic filler.

Revise lyrics before generation if the LLM flags awkward rhythm, weak rhyme, overlong lines, or unnatural CJK wording.

## Fast Workflow

Create a song package:

```bash
musia song init \
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
musia song correct \
  --project-dir data/creative_projects/<song-id> \
  --issues "vocal unclear or endings clipped" \
  --caption-extra "clearer vocal, fewer words per line" \
  --lyrics-file corrected-lyrics.txt
```

Handoff to LALACHAN:

```bash
musia song handoff \
  --project-dir data/creative_projects/<song-id> \
  --audio data/creative_projects/<song-id>/final/selected.mp3 \
  --cover data/creative_projects/<song-id>/assets/cover-16x9.png
```

## Master-Companion Pipeline

Use this as a third opt-in route when the existing full-song and strict
localization pipelines should stay unchanged, but multilingual versions need
more consistency:

```bash
musia master-companion \
  --title "Song Title" \
  --master-language ja \
  --master-audio master.mp3 \
  --run-analysis \
  --target-languages en zh-Hans \
  --control-policy quality-first
```

This route chooses or generates one high-quality master render, extracts beats,
chords, phrase timing, and melody/F0, then creates target-language lyric
adaptation packets, soft full-song companion prompts, and strict SVS handoffs.

Default policy: quality first; change lyrics for rhyme/rhythm/naturalness before
changing melody; allow small melody changes when strict matching hurts the song;
publish strict same-melody outputs only after listening and ASR checks.

## Reusable Script

Primary script:

```text
scripts/musia_song_workbench.py
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
- Same melody is optional when it hurts quality. Prefer high-quality independent ACE/YuE language renders over low-quality same-score vocals.
- If Japanese/Chinese lyric accuracy is poor: shorten lines, reduce kanji ambiguity, increase vocal clarity in caption, try new seed/model, or use a specialized vocal workflow.
- For mixed EN/ZH/JP full-song demos on local open models, prefer one active `mul` sung/phonetic lyric track. If native CJK script collapses or garbles, use pinyin/romaji in the sung input and display native Chinese/Japanese as translations with pinyin/furigana. Document this as a phonetic render, not native-script singing.

## Website Publishing Rule

For any selected Musia song that is not explicitly private or experimental,
prepare the Fun website item before calling the song finished. The default
post-song closeout is:

1. Copy or transcode selected audio to `../MusiaSongs/audio/`.
2. Regenerate `../MusiaSongs/audio.json` and commit/push that repo when publishing.
3. Create or update `website/data/songs/<media-id>/manifest.json`.
4. Create per-vocal lyric JSON with ruby/pinyin/furigana and timing.
5. Add or update the song entry in `website/data/catalog.json`.
6. Add a 16:9 cover at `website/assets/covers/<media-id>-16x9.png`.
7. Run `npm run website:validate`, `musia fun-audit --media-id <media-id>`, `node --check website/app.js`, and `git diff --check`.

If the song will be packaged for LazyEdit/Shipinhao Music or YouTube Music,
the package must use the corrected active-vocal website lyric JSON as its
lyrics source. Do not hand off the original prompt lyric, planned translation,
or master-language transcript to the publisher. The music platform lyrics
should match the corrected `fun.lazying.art` lyric set for that exact audio.

For `fun.lazying.art`, use the `musia-fun-website-item` publication workflow before calling a website item finished. Use shared `textTracks[]` only when all playable vocals truly sing the same line structure. If English, Chinese, and Japanese renders are independent or imperfect, create per-vocal `lyricSets[]`:

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

The active vocal owns timing and exact word highlighting. Other languages in the same set are translations of that vocal's actual sung lines and may rough-highlight corresponding tokens inside the same current `line.id`.

Correct every public lyric set from at least two evidence sources: ASR/STT from the actual vocal plus input/reference lyrics, second ASR, or manual listening. For close word conflicts, preserve the input/reference lyric when pronunciation, grammar, and phrase structure support it; use ASR to detect real structural differences, not as an unquestioned transcript. Add pinyin for Mandarin, furigana readings for Japanese kanji, and Jyutping readings for Cantonese. Run the publication audit:

Also check missing planned phrases before publishing: scan any ASR timing gap
and any unusually long merged ASR segment against the source lyric. Add
sound-supported phrases to the active JSON and matching translation tracks; do
not leave the public site or LazyEdit/Shipinhao handoff using the older
incomplete lyric set.

For companion-language songs, this evidence rule applies to each playable
asset separately. Never reuse the master-language transcript, prompt lyric, or
another vocal's timing as the public lyric source for EN/JP/ZH/Cantonese unless
the selected audio's own ASR/listening pass confirms it.

```bash
musia fun-audit --media-id <media-id>
```

For EN/JP/ZH companion renders, double-check every visible translation track
before publishing. `ja.json` should not silently contain English hooks, and
`zh-Hans.json` / `zh-Hant.json` should not silently contain English hooks,
unless the active vocal truly sang a mixed-language line and the manifest says
so. Use `musia fun-audit --media-id <media-id> --strict` to catch wrong-script
visible text.

The Fun player should keep public song playback clean: native-language dropdown labels, a two-line KTV lyric carousel, visible current-chord highlighting, and capture mode for videos. To record a share clip with the original audio muxed directly, run:

```bash
musia fun-record --media-id <media-id> --skip-intro
```

For a mixed-language vocal, use:

```text
lyrics/mixed-vocal/mul.json
lyrics/mixed-vocal/en.json
lyrics/mixed-vocal/zh-Hans.json
lyrics/mixed-vocal/ja.json
```

## References

Read only as needed:

```text
references/musia-song-generation-and-website-runbook.md
references/fun-website-item-preparation.md
references/musia-song-workbench.md
references/lalachan-song-first-video-workflow.md
references/musia-full-capability-guide.md
references/musia-creative-studio.md
references/musia-website-json-format.md
```
