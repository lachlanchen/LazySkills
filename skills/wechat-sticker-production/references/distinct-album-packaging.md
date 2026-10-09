# Distinct Album Packaging

## Review Lesson

On 2026-10-09, two albums were approved and two rejected. Both rejection notices specifically named reused **album covers** and **chat icons**. A new title or different GIF set does not make reused packaging distinct. Inspect the actual notice rather than assuming the banner was the only problem.

Preserve approved GIF animation. Repair rejected works in place, not by creating duplicate albums. Give each album its own recognizable pose, action, props and scene, not merely a recolor. Keep a separate cover, chat icon, banner, appreciation guide and thank-you export for each volume.

The repaired affection pack uses a shared heart cushion and a coral loveseat scene. The outing pack uses a camera, picnic bag and bright meadow. New artwork was generated from approved character references with the built-in image tool. Original packaging and GIFs remain preserved.

## Export And Validate

`scripts/package_wechat_artwork.py` formats approved transparent cover and landscape banner art, copies existing GIFs byte-for-byte and writes a provenance manifest. Use a new output folder. Inspect the selected icon crop at 50 pixels; do not rely on a large source preview.

```bash
python3 scripts/package_wechat_artwork.py \
  --cover "$ART/cover.png" --banner "$ART/banner.png" \
  --gifs "$ACCEPTED/gifs" --output "$NEW_ALBUM" \
  --icon-box 0.1 0.1 0.9 0.9 --color '#bfe6ed'
python3 scripts/audit_wechat_album.py "$NEW_ALBUM" --expected 16 --title "$TITLE"
python3 scripts/audit_wechat_packaging.py "$VOL1" "$VOL2" "$VOL3" "$VOL4"
python3 -m unittest discover -s tests -p test_wechat_packaging.py
```

The cross-album audit rejects identical decoded artwork even after lossless re-encoding. Perceptual similarity raises a manual-review warning. Passing this check is not a guarantee of platform approval.

## Browser Verification

Bring the existing authorized account tab forward. Replace only the five observed packaging file inputs and wait for each remote image preview to load. Preserve GIF count/order, meaning words, price and appreciation setting. Capture the new previews before one authorized submission, then reopen the same work and verify its status and saved artwork.

An observed Edit button used `window.open(..., '_blank')` and was blocked by the browser. Discover the requested target URL from that interaction and navigate the same tab to it; do not repeatedly click or create a new work.

Separate states: uploaded, saved draft, submitted for review, approved, scheduled, live. Approved is not automatically live: the observed flow required 上架 -> 今日 -> 预约. After one successful reservation, reload and verify 已上架. Never repeat a successful reservation just because a toast/modal remains briefly visible.

New packs requested for owner review stay drafts even when the owner authorizes resubmission of older repaired packs. Appreciation and paid access remain separate controls.

## Review Exports

Use the existing gallery layout and `snapshot_wechat_gallery.py` to export the HTML, GIFs, full-page screenshot and each GIF preview to the configured Nutstore sticker share. Keep account screenshots and submission receipts private and outside that artwork export. Local verified copies do not prove cloud synchronization.
