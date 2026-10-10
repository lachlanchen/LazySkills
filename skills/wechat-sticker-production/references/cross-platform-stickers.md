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
