# Text-Only Sticker Variants

The owner's 2026-10-05 request was to try smaller cute lettering, white with a dark outline, lightly animated and positioned like spoken replies rather than always below the character. Make a separate comparison edition; keep the accepted animation and platform drafts unchanged until the owner chooses.

## Method

`scripts/restyle_sticker_text.py` works on the existing bounded GIFs produced by `video_to_wechat_gif.py`. Their artwork occupies the upper 180 pixels and their old lettering sits in a separate bottom caption band. It is not a general tool for erasing text baked over a character. For other source layouts, use the preserved clean video instead and review the resulting animation explicitly.

1. Read each source's frame sequence, individual delays and palette. Keep a source hash.
2. Clear only the verified old caption band, using the existing background color. Place the new lettering with per-sticker position, size, rotation and horizontal/vertical direction.
3. Supersample glyphs for rounded outlines. The text is always readable; small bounces and tilts add expression without hiding or flashing the reply. Preserve faces, meaningful gestures and borders by reviewing every layout.
4. Hold eight text poses over a loop by default. This changes only the overlay's animation cadence, not the source frame rate or duration. Continuously changing antialiased lettering made some files unnecessarily large.
5. Use the source's shared palette for the text as well. The outline uses its nearest dark tone. Do not requantize character pixels or reduce their frame rate to fit an overlay.
6. Reopen the finished GIF and compare every frame: identical delay sequence and pixel-exact imagery outside the old/new text masks. Optional Gifsicle `-O3` is accepted only after the same decode comparison passes.
7. Audit 240-square dimensions, loop, clipping and 500,000-byte limit. A larger local preview is not ready for WeChat upload. No automatic platform replacement or resubmission follows a successful export.

## Run

Requires Pillow, NumPy, fontTools and optionally Gifsicle. Use an isolated environment when dependencies are missing. No GPU or video-generation service is required.

```bash
python scripts/restyle_sticker_text.py "$ORIGINAL_ALBUM" "$NEW_VARIANT_FOLDER" \
  --layout "$LAYOUT_JSON" \
  --font "$FONT_FILE" --gifsicle "$GIFSICLE"
```

The layout JSON has `title`, `erase_band: [0,185,240,240]` and `items`. Each item specifies `file`, `label`, `center: [x,y]`, `font_size`, optional `vertical`, `angle`, `bounce`, `wiggle` and `motion_steps` (default eight). Include exactly the filenames in the source `gifs/` folder. Review placements for that album rather than copying another album's coordinates.

The output contains `gifs/`, byte-identical copies in `originals/`, first-frame PNGs, per-GIF provenance, `audit.json`, a layout copy and an offline `index.html`. The gallery switches between original and variant and includes a chat-size preview. Existing outputs are never overwritten; partial experiments remain separate from the selected complete edition.

For this trial the font is [ZCOOL KuaiLe](https://github.com/googlefonts/zcool-kuaile), supplied under its repository's SIL Open Font License. Keep the license with downloaded font files. Verify every requested character exists in the font; do not substitute missing-glyph boxes or generated lettering.

## Review and Sync

Open the full gallery persistently in the existing review browser, and the variant folder in the owner's physical desktop file manager. Select the physical desktop environment explicitly so a noVNC session does not capture later file opens. No new desktop stack is needed.

Review full and chat size, all 24 placements and several animation phases. Export to a separate `Share/Stickers/Vol-04-text-cute-v1` folder, including the `originals/` comparison files. Use the existing `snapshot_wechat_gallery.py` for a full-page screenshot and one screenshot per GIF; its artwork allowlist does not copy `originals/`, so copy and verify that directory separately. Keep account pages and financial receipts out of the export. Local hash verification is not a cloud-sync acknowledgement.

## After Owner Approval

For this owner, the cute-text style became the future default after review. Keep submission authorization separate from aesthetic acceptance. Saved-draft card deletion controls appeared on hover even when old meaning-word inputs looked disabled. Replace form items, not the album; preserve old local files. Count meaning-word inputs rather than `[isfirstcrop]`, which was absent on new upload cards. Verify an empty form before selecting the sorted replacement batch, then wait for all thumbnails and inspect order/labels.

For an authorized paid release, select the actual price control and retain appreciation. Save once and inspect a separately reloaded settings page for count, price and appreciation; then submit once and verify pending-review status. A saved draft, successful submission, payout-information approval and published availability are distinct states. Keep account receipts outside shared artwork exports.
