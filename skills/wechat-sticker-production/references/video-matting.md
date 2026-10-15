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
The 2026-10-16 CPU prototype is experimental, not an automatically approved
batch-replacement pipeline. Existing live listings remain unchanged.
