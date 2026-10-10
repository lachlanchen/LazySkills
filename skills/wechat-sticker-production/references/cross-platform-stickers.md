# Cross-Platform Sticker Delivery

Export selected approved animation, not private production folders. A format or
language edition is the same animation and does not count as a new action.
Keep account approval, media upload, review, search indexing and live install
links as separate states. Reuse the owner's authorized browser and existing
packs; do not create a new account or duplicate draft merely to recover a timeout.

## Telegram

The official `@Stickers` bot accepts VP9 WEBM: no audio, at most three seconds,
one side exactly 512 pixels, at most 30 fps and 256 KB. Check current official
[specifications](https://core.telegram.org/stickers) before a new production run.
Retiming should preserve the complete gesture, not cut the ending. Validate
decoded alpha, not just its container flag, and inspect white fur, lettering and
robot panels against dark backgrounds. Record compression and fps compromises.

The LALACHAN repository provides:

- `scripts/export_chat_stickers.py`: immutable, checksum-verified Telegram/GIPHY
  derivatives, per-item manifests, ZIPs and light/dark preview galleries.
- `scripts/upload_telegram_stickers.mjs`: appends approved files through the
  observed Telegram Web Document chooser, with a file/emoji/count receipt cycle.
- `scripts/publish_telegram_sticker_batch.mjs`: serially creates reviewed packs,
  completes upload, selects the first sticker as icon and records published links.

Supply the Playwright module and authorized CDP endpoint through environment
variables, and all media/configuration/state paths as arguments. Keep peer IDs,
account screenshots and upload receipts in an ignored private runtime folder.
Run only one worker in the bot conversation. A pending send is not safe to retry:
inspect the live bot response and reconcile the last accepted count first.
Unexpected replies halt the batch rather than creating another pack.

Choosing Document before using its file chooser is important. Setting a hidden
file input directly did not initialize Telegram Web's send mode. Check the Send
File modal's filename, send once, wait for the emoji request, then send one or
two matching emotion emoji. Count confirmation is the item receipt. Publish only
after every expected item is accepted, and keep the returned install URL.

These custom packs use free sharing links. There is no native pack retail price
field in this flow; do not confuse Telegram Premium with creator pack sales.

## GIPHY And Other Platforms

LazyingArt uses a GIPHY **brand** application, not a non-commercial artist claim.
The account needs an avatar and at least five public uploads before application.
Use relevant expression/character tags and an actual owned source website.
Be truthful about AI-assisted origin. An application submission and public GIF
URLs do not establish Instagram partner-search availability.

For this owner's Aya/Lala collections, use `ayalala` and `lazyingart` as common
search tags, with relevant expression tags in addition. The verified channel is
`@lazyingart`; preserve its handle. Report tag-save success separately from
GIPHY/Instagram search eligibility. Existing uploads can be tagged through their
Edit UI without creating duplicate GIFs; verify the tags after reload.

The owner requests a small `@lazyingart` corner credit on future GIPHY GIFs.
Choose a quiet corner using the entire motion, keep the credit fixed, and check
chat-scale legibility on light/dark backgrounds. Export to a new edition folder.
The current editor lacks a media-replacement control; preserve existing posts
and apply this preference to future uploads rather than deleting old content.

Tenor's website accepts at most ten files per batch. Its preview order can
differ from file-input order: match preview blob hashes to source hashes before
assigning expression tags. Save intent before one Upload click and reconcile
the profile afterward. Processing, pending review and publicly searchable are
different states. Inspect rejection notices for the exact item before retrying;
a generic technical rejection does not prove every file failed. The LALACHAN
`normalize_tenor_gif.py` helper creates a new full-frame transparent GIF and
checks exact timing, dimensions and full decode. Repost a corrected rejected
item once; preserve accepted/pending files and all originals. If it fails again,
use support/appeal instead of repeated re-encoding uploads. Keep authenticated
media URLs private because their query strings can contain credentials.

The successful upload page can remain at `/upload/finalize`. Verify the
expected number of `Open Sticker` links and `Open Channel`; a navigation
timeout is not an upload failure and must not trigger another submission.
Keep an intent receipt before clicking Upload and reconcile completed links
after interruptions. Add tags one at a time through the visible add button,
waiting for the input to clear. Save the source URL and check public visibility.

For new multilingual packs, localize the approved clean native clips rather
than relabeling an already lettered GIF. The LALACHAN
`localize_sticker_selection.py` helper reuses the shop's word-aware English
renderer; square CJK character spacing is unsuitable for English. Review
longer labels over the complete motion and preserve earlier exports.

For LINE, `stage_line_sticker_pack.mjs` saves an explicit metadata/asset edition;
`submit_line_sticker_review.mjs --confirm-review` separately requests review.
Both take private receipt paths and the installed Playwright module through
configuration. Inspect the actual lowest price and auto-release setting, then
reload to verify `Waiting for Review`. In WeChat a taken album title should be
corrected on the same draft, not by creating a duplicate work.

Telegram, GIPHY, LINE and WeChat have different formats and commercial models.
Do not invent a paid tier where a platform offers free sharing only. Check
eligibility before preparing submissions: Zalo's published guide conflicts with
the current 3D figurine style, and Kakao's guide restricts generative-AI work.
Preserve accepted artwork instead of silently changing its style for eligibility.

## Review-Only Packs

When local animation cannot pass its resource gate, prepare and inspect the
references without calling them finished GIFs. A preview should show actual
animated/total counts. Keep active virtual machines and other projects intact.

Inspect generated contact sheets before cropping. Their visual divider may not
be at the arithmetic midpoint. `prepare_line_extensions.py --row-split-y` can
use a reviewed boundary in a new versioned root. Preserve old crops, and make
the renderer consume the corrected manifest rather than only updating a gallery.

An approved public reference preview can be deployed independently of a shop's
paid catalog. Use an explicit artwork allowlist, verify ZIP/file hashes, retain
the prior immutable release and rollback if live checks fail. Do not export
private sidecars or account receipts. A copied Nutstore folder is not proof of
cloud acknowledgement.
