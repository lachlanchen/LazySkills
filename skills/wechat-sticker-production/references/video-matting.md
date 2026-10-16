# Moving Sticker Transparency

White background removal is semantic video matting, not a format conversion.
White robot panels and enclosed white background gaps require opposite labels;
color thresholds cannot distinguish them. Global hole filling is not a fix.

- Start from the preserved native animation, before text. A damaged GIF cannot
  recover deleted body pixels. Preserve all candidate editions separately.
- Use positive subject/part masks and negative true-gap labels. Propagate with
  motion and visibility checks; re-anchor uncertain frames. Keep small genuine
  holes instead of relying on a segmenter's automatic hole-filling option.
- Separate hard interior identity from soft boundary refinement. A stronger
  segmenter can still erase a head; a high predicted score does not prove its
  geometry. Inspect worst moving frames and light/dark composites.
- Hold uncertain results rather than promoting a plausible mask automatically.
  Conservative part protection can leave a ghost if tracking drifts, so it also
  needs review. Flow agreement alone is not ground truth.
- Store straight-alpha RGBA masters. Add lettering afterward. Conversion to
  LINE APNG must preserve alpha, including during RGB palette reduction.
  GIF binary alpha is a separate compromise. Decode the actual output to check.
- Test same-color parts, enclosed/opening gaps, thin limbs, overlaps and blur.
  Distinguish synthetic exact-alpha tests, manual core labels and whole-frame
  real quality. Never report a toy benchmark as full-catalog accuracy.
- Respect model licenses: SAM 2 / ViTMatte / PyMatting are practical candidates;
  MatAnyone 2 and VideoMaMa have noncommercial restrictions. Verify weights too.

LALACHAN research implementation and runbook:
`references/wechat-stickers/matting-research/README.md`.
The initial 2026-10-16 CPU/SAM 2 prototype is experimental. The later catalog
repair reviewed 296 native animations with BiRefNet-lite semantic proposals,
motion-gated smoothing and PyMatting boundaries. That is a supervised production
workflow, not a newly trained model or guaranteed automatic cutout service.

## Catalog Repair Lessons

- Preserve the native RGB animation and source hash. Cache semantic predictions;
  one reviewed RGBA master feeds every language/platform instead of re-keying
  an already damaged GIF. Native animation and caption changes are separate.
- Review dark and colored composites at several phases, then inspect decoded
  platform output. White panels, tabletops, blankets, cables and effect marks
  were common failure cases. Segmenter confidence alone did not catch them.
- Apply local source-bound correction only where needed. Positive/negative
  temporal anchors require motion confidence; textureless solid surfaces may
  need explicitly corresponding geometric anchors at both endpoints and motion
  changes. Preserve the rejected candidate and review the corrected motion.
- A baked white vignette cannot be exactly inverted. Four office exports used
  an explicitly documented approximate bottom-fade reconstruction. Do not call
  this recovery of missing legs or apply it generally to white characters.
- LINE preserves soft alpha even during palette compression. Validate opacity
  at source time samples because identical adjacent APNG frames may merge.
  LINE's maximum four-second playback is not an infinite-loop format.
- Bind candidate approval, caption choice and delivery to hashes. Hold partial
  encodes in their original folder; use a new edition for recovery. A remote
  upload intent without a result requires reconciliation before another send.
- Serialize shared-CDP controllers and bring the active platform tab forward.
  GIPHY six-item batches avoid excessive decoding memory; Tenor accepts ten in
  the qualified uploader. Telegram replaces exact snapshotted document IDs and
  retains the pack URL. Never change paid-pack pricing or create paid duplicates
  simply because a platform cannot replace approved artwork.
- Export an artwork-only portable history gallery and verify copy hashes.
  Platform receipts, account screenshots and private paths do not belong there.
  Local Nutstore copying is not proof of cloud acknowledgement.

Full commands, model pin/license, tests and limitations:
`references/wechat-stickers/matting-research/catalog-repair-20261016.md`.

Owner preference: new GIPHY editions have **no visible @lazyingart credit**;
retain account/search tags. Preserve earlier credited posts unless separately
authorized for retirement. This supersedes the earlier corner-credit preference.

On 2026-10-16 the owner clarified that existing artwork may stay unchanged when
the platform cannot replace it. Use reviewed alpha masters for future exports;
do not treat account login as approval to unlist or duplicate an existing pack.
Keep prepared repairs and prior editions. For an already running upload queue,
finish and reconcile the in-flight submission before stopping further batches.
