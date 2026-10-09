# Independent Sticker Editions and Gallery

## What Was Finished

The 2026-10-09 independent-edition repair covered six newer packs: 闪光的日常, 空耳小日常, 得闲陪你倾, 运动五分钟, 实验室小心情 and 小车开到你家. Their existing works were updated and submitted, then verified as pending review with 10 Beans and appreciation accepted. Review submission is not approval or publication.

The selected-source audit covered 156 stickers across ten packs: 156 distinct native files, no repeated source hashes and no missing files. Five-role packaging checks passed across all ten packs. Account identifiers, screenshots and upload receipts remain in private runtime/output folders.

The gallery redesign did not change the established reference-image, local-animation or cute-text pipeline. Accepted color/expression differences and funny deviations were retained. No submitted work was withdrawn to adjust those aesthetic differences.

## Three Different Comparisons

1. **Formal animation uniqueness:** inspect the selected native MP4 sources across packs. New lettering, language, crop, frame rate or encoding does not create a new animation. Native hashes catch exact reuse; inspect motion/contact sheets as well because a separately encoded copy has a different hash.
2. **Historical export identity:** gallery archival indexes distinct GIF bytes, so different text/layout/palette editions remain accessible. Identical copied exports are indexed once. No native files or old exports are deleted.
3. **Visual acceptance:** distinguish actual identity/anatomy failures from accepted expressive exaggeration or color variation. For example, the old and new sports 有点重 editions used the same native animation; their GIF frame rate/palette differed. That was not an extra motion generation.

Targeted local corrections retain their original reference, request, receipt, MP4 and GIF in a versioned candidate folder. Archive visible deviations honestly and choose the reviewed candidate. A preflight rejection is not a completed GPU render; correct the specific contract or wording without disabling its guard.

## Future Reference Consistency

For a new pack, compare the references together before animation. Use the approved Aya red-orange palette and consistent neutral white balance, retaining material detail and the intended clothes. Keep Lala's familiar face while allowing readable expressions. A warm scene and a reduced GIF palette can each alter apparent color, so compare the reference, native frames and final GIF separately.

The owner accepted the existing muted Aya variants and exaggerated sports expression. Preserve them, including submitted editions. Improve future inputs instead of retroactively rerendering accepted work.

## Gallery Structure

`build_sticker_library.py` creates an offline site using `sticker_library.html`, `sticker_gallery_viewer.py` and the vendored Lucide subset in `sticker_icons.py`. No runtime package or CDN is needed. The icon license is exported beside the page.

- Current selections: the formal chosen edition of each pack.
- Historical versions: earlier text, crop and animation exports.
- Alternatives: accepted funny candidates and disclosed deviations, separate from formal uploads.
- Search and series selection, chat-size preview, GIF download, a modal viewer, keyboard arrows/Escape and browser Back.
- Direct sticker links reopen the right historical collection instead of an empty filtered viewer.
- Responsive desktop sidebar and mobile horizontal navigation. Image/card dimensions remain stable.

The private review build contained 478 entries when checked: 156 current, 317 historical and 5 alternatives. These are export counts, not 478 distinct formal animations.

## Reusable Commands

Keep local paths in private configuration or environment variables. The library config uses pack entries with `id`, `title`, `folder`, `status`, and optional `expected`, `group`, `labels` and `notes`. `folder` is the album directory containing `gifs/`; run from the directory against which relative folders resolve. Use `group` values `current`, `archive` or `alternatives`.

```bash
python3 scripts/audit_wechat_animation_reuse.py "$SELECTION_CONFIG" "$NEW_NATIVE_REPORT"
python3 scripts/audit_wechat_album.py "$ALBUM" --expected 12 \
  --title "$PACK_TITLE" --labels-file "$SELECTION_JSON"
python3 scripts/sticker_review_sheets.py "$ALBUM/gifs" "$NEW_REVIEW_FOLDER"
python3 scripts/audit_wechat_packaging.py "$ALBUM_ONE" "$ALBUM_TWO"
python3 scripts/build_sticker_library.py "$LIBRARY_CONFIG" "$LIBRARY_DIR" \
  --archive-root "$STICKER_ROOT"
```

`archive-root` scans artwork GIFs, omitting the current output, capture/review-sheet folders and byte-identical copied exports. Keep the supplied root limited to the sticker project, not Downloads or unrelated private media.

For each album, reuse the existing local-gallery CDP tab to capture the full HTML page and one preview per GIF:

```bash
python3 scripts/snapshot_wechat_gallery.py "$ALBUM" "$SYNC_ALBUM" \
  --cdp-url "$CDP_URL" --page-id "$GALLERY_PAGE_ID"
```

This copies only allowlisted artwork, GIFs and gallery captures, then compares SHA-256 values. It does not export account pages or upload receipts. A matching local Nutstore copy is not proof of cloud acknowledgement. Preserve timestamped captures and existing editions; copying should not delete them.

For the combined library, copy its generated `index.html`, `audit.json`, `LICENSE-icons.txt` and `gifs/`, plus artwork-only review screenshots. Keep album return links correct for the destination depth. Open the copied HTML and validate its relative GIF paths.

## Public Preparation, Not Deployment

Ordinary review builds include unpublished editions and review notes. Do not deploy the private review directory. Explicitly mark approved packs `public: true` and export to a **new empty directory**:

```bash
python3 scripts/build_sticker_library.py "$LIBRARY_CONFIG" "$NEW_PUBLIC_DIR" --public-only
```

This includes only opted-in current packs, removes private notes and review status (unless a `public_status` is supplied), and excludes archives and unapproved packs. It fails on an existing nonempty destination to prevent old review assets leaking into the public package. Review titles, labels, image content and deployment permission separately; this flag does not anonymize intentionally supplied public text or publish a site.

## Verification

```bash
python3 -m unittest discover -s tests -p test_sticker_library.py
PLAYWRIGHT_MODULE="$PLAYWRIGHT_MODULE" node tests/sticker_gallery_browser.cjs \
  "$LIBRARY_DIR/index.html" "$NEW_SCREENSHOT_FOLDER"
```

The repository fixture exercise covers sports filtering, modal navigation/Back/Escape, mobile bounds, archive deep links, empty search and keyboard edition tabs. Python tests cover archive deduplication, retained exports, escaping, receipt exclusion, explicit public selection and refusal to reuse a private output directory. Visually inspect screenshots as well.

When renders finish, stop only the verified owned idle model services. Retain the shared browser needed for user review; preserve other projects, VMs and all generated artifacts.
