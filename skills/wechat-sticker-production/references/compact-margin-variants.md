# Compact Sticker Margins

## Purpose

Reduce the large border and reserved caption strip using existing clean native
animations. This is postprocessing, not a new image or video generation. Keep
accepted originals and use a separate preview edition until the owner chooses.

The older converter fits artwork into the upper 180 pixels of a 240-square GIF,
then reserves a bottom caption band. Cute lettering alone leaves that composition
unchanged. A compact edition instead crops the original clean MP4 and places
lettering beside the action.

## Export

Requires FFmpeg, Python, Pillow, NumPy, fontTools and a licensed font with all
requested glyphs. Gifsicle is optional. No GPU or model service is needed.

```bash
python scripts/compact_wechat_sticker.py "$CLEAN_MP4" "$NEW_DIR/compact.gif" \
  --label 委屈 --font "$FONT_FILE" --padding 10 --gifsicle "$GIFSICLE"
python scripts/compact_wechat_sticker.py "$CLEAN_MP4" "$NEW_DIR/edge.gif" \
  --label 委屈 --font "$FONT_FILE" --padding 1 --gifsicle "$GIFSICLE"
```

These padding values are comparison choices, not new universal defaults. The
canvas remains 240 x 240. Aspect-ratio fitting can leave space on one axis;
"edge" does not mean stretching, cutting a limb, or filling every pixel.

1. Use a white-background animation without lettering over the character. Keep
   the original MP4 and all existing GIF editions. This helper is not background
   removal and does not erase text already baked over a face.
2. Detect a foreground box across **all extracted frames**, with a small safety
   inset. Use that single crop throughout the loop, avoiding changing zoom or
   clipped moving limbs. White-on-white details and shadows still need inspection.
3. Scale proportionally. Place the approved small rounded white/dark-outline text
   at a low-overlap corner or side, with restrained bounce/tilt. Evaluate the whole
   action and multiple text phases. The default rejects overlap above 2%; this
   pixel proxy is not a face detector or a substitute for visual review.
4. Use `--center X Y`, `--vertical`, or `--font-size` for a deliberate adjustment.
   Revise a crowded layout rather than accepting text across eyes or a gesture.
5. Encode below 500,000 bytes. The helper tries palette reductions before lower
   frame rates. Optional Gifsicle `-O3` is used only when decoded pixels and timing
   remain identical to that encoded candidate. **The overall crop/resize/palette
   process is not lossless**, and lower frame rates must be disclosed.
6. Read the sidecar JSON: source/font/output hashes, fixed crop, text location,
   overlap estimate, duration, selected rate/palette and encoding attempts.
   Failed exports leave originals untouched and must not trigger model rerenders.

The duration/speed defaults match existing five-second sticker sources: 5.125
seconds of source at 1.25x, approximately 4.1 seconds per loop. Use explicit
arguments for other sources. Export always requires a new output path.

## Compare And Verify

`build_sticker_margin_review.py` accepts a JSON file with `title` and `items`.
Each item has `label`, `original`, `compact`, and `edge` input paths. Paths belong
in local configuration; the generated portable gallery includes only copied
artwork and hashes, not source-machine locations.

```bash
python scripts/build_sticker_margin_review.py "$COMPARISON_JSON" "$GALLERY"
python scripts/snapshot_wechat_gallery.py "$GALLERY" "$SYNC_DESTINATION" \
  --cdp-url "$CDP_URL" --page-id "$EXISTING_GALLERY_TAB"
python -m unittest discover -s tests -p test_sticker_compact.py
```

The original/compact/edge columns use the approved gallery palette and include
240-pixel and 120-pixel views. A new folder is required; all input GIFs are copied
byte-for-byte. Every included GIF must loop at 240 square and meet the byte limit.

Review at least three loops and several motion extrema: ears, tail, feet, hands,
text edges and face visibility. Inspect the small chat size, not just enlarged
stills. Check desktop and narrow layouts, and restore temporary viewport overrides
after screenshots. A gallery screenshot captures one phase, not the whole loop.
Use the existing CDP gallery tab for a persistent preview without opening another
browser/desktop stack. Export the HTML, GIFs and screenshots to a separate Nutstore
folder, verify local hashes, and distinguish copying from cloud acknowledgement.

## First Trial, 2026-10-09

Three actions were compared: Aya's 委屈, Lala's 汗, and Zhuangzi's 好. Two tighter
layouts each gave six new variants, plus three baseline comparisons. All nine
GIFs fit 500,000 bytes. New variants were 382,763-490,734 bytes at 10-15 fps;
original comparisons were approximately 15 fps. The sampled poses kept lettering
clear of faces and meaningful gestures; compact characters were visibly larger.

The Aya/Lala baseline comparison received the same cute outlined lettering while
retaining its older artwork area. Zhuangzi used the accepted cute-text edition.
Early local encoding attempts and all original animation sources remain preserved.
None of these comparison variants replaced platform artwork or changed review state.
