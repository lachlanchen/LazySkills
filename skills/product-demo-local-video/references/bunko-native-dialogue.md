# Tested reference: Bunko Chinese introduction

The owner approved the sound and video on 2026-10-14 and requested only smaller App Store/Google Play icon treatments at the end. This is one successful recipe, not evidence that any one setting caused the improvement or that every render will succeed.

## Performance baseline

| Setting | Verified value |
| --- | --- |
| Engine | LocalVideoGen local H3 |
| Mode / profile | `r2v` / `quality_int8_offload` |
| Sampling | 25 steps |
| Native picture | 704 × 1248, 24 fps |
| Request / aligned length | 14 seconds / 345 frames = 14.375 seconds |
| Seed | 202610143; provenance, not a universal preferred seed |
| References | Four separate approved character images; no audio reference |
| Audio contract | `audio_intent: conversation` and explicit speaker/text dialogue |
| Final edit | 19.4 seconds, 1080 × 1920, 30 fps; native scene plus real UI and end card |

Obtain these fields through the **current** LocalVideoGen parser rather than pasting a stale graph. In the successful run, `parse_render_spec(..., require_audio_contract=True)` and `compile_prompt(spec)` validated the payload before a single submission. Use current documentation for URLs, schemas, model availability and admission gates.

Four buddies: Lala Xia (giant panda), Aya Chan (red panda), Sasa Kun (human boy in a panda hood, not an animal panda), and Zhuangzi (small articulated robot). Exact approved images were reused. Only Sasa and Aya spoke.

## Scene and native dialogue

Warm afternoon reading nook. Sasa holds one phone; Aya sits beside him. Lala and Zhuangzi react behind them. Sasa gets stuck, Aya points down the same page, Sasa wants to try again. A small motivated push toward the phone motivates a cut to real Bunko pixels. Keep generated phone surfaces plain; never rely on the model to render the app.

> Sasa: 这句，我有点没看懂。
>
> Aya: 往下看，中文就在下面。
>
> Sasa: 哦，那下一句我自己试试。

Useful delivery direction: native Mandarin, softly expressive and close; natural young-boy voice and warm young-adult female voice; ordinary pacing and brief pauses; no shouting, infantile squeaking, narrator or announcement cadence. The listener's mouth should stay at rest while the other speaks. This is a direction, not a claim of verified canonical voice cloning.

Keep hand ownership simple: one phone in Sasa's left hand, Aya points without taking it. Subtle posture, gaze, cloth/fur and robot-head reactions keep non-speakers alive without competing with the demonstration.

## What the raw generation got wrong

The first and only generated source included a duplicate opener, an unclear extra line, and an invented phone screen. Built-in expected-dialogue coverage was 1.0, yet it was **not** acceptable unedited. Independent cached large-v2 Mandarin ASR exposed the extra material.

The approved edit retained native 24 fps frame ranges `[0, 60)` and `[194, 345)`—211 frames, about 8.792 seconds. Matching audio ranges were cut with tiny edge fades. These frame ranges apply only to this source; derive new boundaries from every new performance.

The final retained transcription matched all three intended lines after punctuation and Traditional/Simplified normalization. No new voice, speed change or expensive regeneration was needed. Raw source remains evidence, not a publishable master.

## Genuine demonstration and finish

- English then Chinese reading layers, with pinyin, recorded from the actual Bunko browser reader at 1260 × 2220. The Japanese book title stayed visible; it was not a third reading layer. The English study translation was not called original English text.
- Final timeline: approved performance 0–8.8 seconds; real-reader reveal inside it at 3.8–5.85; continuing real passage 8.8–15.8; end card 15.8–19.4.
- Large Bunko icon/name top-left on a transparent background; brief opening hook. No burned dialogue subtitles in this review master; corrected Chinese SRT supplied separately.
- Quiet existing Musia instrumental under the native conversation and reader. Full decode passed; measured final peak −5.5 dBFS. These are reference results, not mandatory mix targets for all products.
- Owner's final refinement: remove filled store rectangles, use recognizable App Store/Google Play icons with small labels. Keep the product and benefit visually dominant.

When only revising the end card, concatenate the existing encoded performance and reading-tail segments with the new card, then mux the **original accepted audio stream using `-c:a copy`**. Compare the audio packet SHA-256 and decoded frame hash of the unaffected prefix. Inspect the new boundary and decode the entire revised file. Do not introduce a new audio mix just to change a store icon.

## Reuse without overgeneralizing

The likely contributors were a bounded two-person exchange, joint audio/video generation, explicit natural delivery, full-quality local settings, and careful editing around real UI. This was not a controlled comparison with earlier videos: do not attribute success solely to 25 steps, the seed, or a different engine.

For another app, replace the actual problem, action, truthful outcome and capture; retain the small story and evidence-first construction. Example: pronunciation practice should show the actual listening/scoring interaction, not just a phone held by a mascot. Music software should let its musical result be heard. Do not clone the same reading joke into every product.

Private Bunko source scripts, exact approved reference paths and receipts are in LazyPromotion's `.local/private/bunko-chinese-local-20261014/`. The portable skill contains no credentials, runtime identities, private session extracts, model weights or generated media. Do not commit those artifacts when following this recipe.
