---
name: wechat-sticker-production
description: Create and review a consistent WeChat sticker series, animate approved character references with LocalVideoGen, convert owned video into bounded GIFs, and upload singles or albums through an authorized WeChat Sticker Platform browser.
---

# WeChat Sticker Production

Use this for the WeChat Sticker Platform, not WeChat chat-message automation or social video publication.

## Design and review

For this owner, each selected formal sticker must have a distinct animation across packs. Changing lettering, language, crop or encoding is not a new animation. Run `audit_wechat_animation_reuse.py` on selected native sources and visually compare actions; exclude archived alternatives and text revisions of the same sticker. Packaging/file hashes alone miss this failure. New editions must not reuse another pack's selected animation.

Define a small series around common chat replies. Each sticker should work alone, while shared clothes, palette, character relationships, or a small daily-life arc connect the set. Prefer one or two clear subjects, a large expressive face, a simple backdrop, and one readable action. Learn from public sticker collections without copying their characters or assets.

For this owner's future cross-platform packs, use 16 distinct animations by
default, or 24 for a fuller theme. Verify current animated-pack limits on each
target platform before rendering. Choose the portable count up front rather
than padding 12/20-item packs later. Already prepared or approved exceptions
stay intact unless the owner requests a count change.

For LALACHAN, inspect the canonical individual images first. Aya is the red panda in a navy sailor outfit; Lala is the black-and-white panda. Preserve the user's approved reference, including prior versions. Do not force every buddy or branded prop into every sticker.

Work one sticker at a time when requested: reference -> user/style acceptance -> local animation -> small-size/loop review -> upload. Planned stickers are not generated stickers. Later cute-angry interactions can form reply pairs such as 哼 / 给你 / 好吧 without becoming hurtful or requiring the full story to understand them.

If the user requests a whole first album, the pilot is a style checkpoint, not the deliverable. Establish a complete 8-24-sticker scope using the live platform limits, then finish that scope sequentially. User additions such as hugs, kisses, shyness and encouragement can extend the same album. Keep each GIF useful independently and do not force all four characters into every composition.

The first still must already communicate the emotion. Inspect at 240 px and chat-like 120 px, with audio absent. Check character identity, limb count, expression, text, crop, motion, and three repeated loops. A smooth global image wobble is not a substitute for a character acting.

For this owner's conversational stickers, prefer articulated acting over a rigid
turntable rotation: a beckoning elbow/wrist, questioning eyebrows, a small nod
or a balanced step with visible knee/ankle movement. Keep the face readable;
describe which joints move and how the weight settles. A spin is appropriate
only when it serves the intended action. Review the middle of the clip, not
just its matching first/last frames. When replacing a mechanical turn, retain
the old native clip and GIF in the existing deviation-candidates gallery with
its original provenance; show the new version separately before distribution.

An owner may find an unexpected detail funny and accept it. Record that specific selection alongside the visible deviation; do not silently replace it or call it perfectly faithful. Preserve any separately authorized alternate for comparison. Acceptance of one variant is not a blanket quality waiver for the rest of the series.

For future references, use one approved character palette and neutral lighting within each pack. Compare Aya's red-orange fur before animation; scene lighting and GIF palette reduction can both change its appearance. Preserve color/expression differences the owner accepts, particularly in submitted packs. A website redesign should not change the successful generation prompts or animation pipeline.

For this owner, retain every generated candidate, including wrong versions, native clips, references and receipts. On 2026-10-09 the owner authorized targeted local corrective rerenders without per-item questions, with the agent selecting the reviewed version that matches the intended identity/action. Keep unsuccessful candidates in a separate `deviation-candidates` gallery category with explicit issues and provenance. Inspect between attempts; normally cap at two corrective attempts, then hold unresolved items and continue others rather than retry indefinitely. This does not authorize paid video rerenders or change draft/review boundaries. An accepted funny deviation can seed a new themed pack with fitting captions; record the changed selection without rewriting the original quality finding. Reuse of existing animation must be disclosed rather than called a new render.

## Local animation

Discover the current LocalVideoGen API and its resource policy from the installed repository. Use its validated image upload and render API, keep the accepted reference as first frame, optionally as final frame for a loop, and save the job ID immediately. Submit each attempt once, monitor that same ID, download its observed output, and fully decode/sample it. A corrective attempt requires inspection and a new versioned spec explaining the change; the owner's local correction permission above is not transport-retry permission.

Check RAM, swap, GPU and queue before rendering. Small output dimensions do not eliminate model-loading memory. Keep the normal resource gates; clean up only verified owned idle runtimes. Never close an active VM or another project's service just to fit a render. Stop the render services you launched when finished, while preserving a browser or image viewer needed for user review.

If RAM is unexpectedly scarce, inspect duplicate noVNC viewer tabs as well as
model processes. Use Chrome Task Manager to match tab titles to renderer PIDs;
high RSS alone does not prove a process is disposable. Close redundant viewers
of the same project desktop while retaining one review view, its noVNC server
and the actual logged-in remote browser. Recheck memory after pages are released
and rerun the unchanged resource gate. A viewer can consume many GiB without
being the browser that owns the task or its login.

Bundled `scripts/render_wechat_sticker.py` supports the local H3 API contract used by this workflow. It records submission intent and receipt, fingerprints inputs, and resumes the same job after interruption. An ambiguous POST is blocked from automatic retry. An explicit preflight rejection is not a completed GPU attempt; preserve that evidence and correct the actual prompt/contract before resubmitting. Do not disable a guard just to get past it.

## GIF packaging

Bundled helper: `scripts/video_to_wechat_gif.py`. Requires Python 3.11+, Pillow, FFmpeg, and an explicitly supplied CJK font when text is used.

```bash
python3 scripts/video_to_wechat_gif.py INPUT.mp4 OUTPUT.gif \
  --duration 5.125 --speed 1.25 --fps 15 --label 哈哈 --font "$CJK_FONT"
```

It creates a GIF, preview PNG and provenance JSON without overwriting earlier versions. Recheck quality after palette/fps reduction. Flat backgrounds often look cleaner with no dithering; this is an aesthetic choice, not a universal rule. Keep the native source MP4, even though GIF carries no sound.

For a wording-only revision, reuse that MP4 and export a new labeled GIF. Preserve both alternatives, ask for selection when requested, and keep just one in the album's numbered GIF folder. Changing `靠山` to `撑腰` does not require a video rerender or a 25th album item.

The owner's Japanese meme-pack preference is Chinese phonetic lettering, not kana. Keep the earlier Japanese-script edition; create a separate text-only version and use Chinese meaning words for search. Treat playful approximations as jokes, not pronunciation tuition or a universal platform language rule. See [series expansion and review](references/series-expansion-and-review.md) for the researched examples and selected-clip workflow.

For this owner's Cantonese pack, GIF lettering stays Cantonese while platform meaning/trigger words are ordinary Mandarin (唔該 -> 麻烦你, 好攰 -> 好累, 冇問題 -> 没问题). Check glyph coverage before exporting; the existing accepted Cantonese GIFs are correct. A missing-glyph error in a new export does not imply the old artwork is wrong. Use the verified Hong Kong CJK font for those glyphs while retaining white fill, dark outline and gentle animated lettering.

For a text-style-only comparison, retain the original frames and timing where a verified separate caption band permits it. The bundled `restyle_sticker_text.py` overlays smaller outlined lettering at per-sticker positions and checks decoded non-text pixels and frame delays for exact equality. It needs Pillow, NumPy and fontTools; Gifsicle is optional for verified lossless compression. Use an explicitly licensed font with complete glyph coverage, keep motion gentle and review faces/gestures at chat size. The output folder must be new. See [text-only variants](references/text-only-variants.md); a local preview does not authorize replacing uploaded drafts.

For this LALACHAN owner, the cute-text comparison style was approved on 2026-10-05 and is now the default: small rounded white lettering, dark outline, gentle bounce/tilt and per-sticker placement around the action. Preserve earlier versions and accepted character animation; fit text to expressions rather than always placing it at the bottom. This preference does not authorize release of a pack the owner wants to review first.

When the owner asks for less margin, use the existing clean animation for a separate compact-layout comparison rather than rerunning a model. `scripts/compact_wechat_sticker.py` uses one motion-union crop and places cute lettering beside the action; `scripts/build_sticker_margin_review.py` compares original/compact/edge layouts. Cropping and encoding are not pixel-lossless: disclose palette/frame-rate changes needed for the GIF byte limit. Inspect several loops at chat size and keep platform artwork unchanged pending selection. See [compact margins](references/compact-margin-variants.md).

The owner's latest 2026-10-09 choice is **edge / 贴边版 for formal publication**, superseding the earlier compact selection. After obtaining the clean native animation, use `compact_wechat_sticker.py --padding 1`: larger characters, a small safety inset, and lettering around the action instead of the older converter's 180-pixel artwork plus caption band. Keep the entire movement/text inside the canvas and adjust padding when necessary. Preserve compact/original editions; existing submitted packs remain untouched unless replacement is separately requested.

Read the current [WeChat official specifications](https://sticker.weixin.qq.com/cgi-bin/mmemoticon-bin/readtemplate?t=guide/index.html#/makingSpecifications#specifications_stickers). On 2026-10-04 a dynamic single used 240 x 240 GIF, looping, <=500 KB. This helper conservatively targets 500,000 bytes. The meaning word allowed four Chinese characters. Albums required 8-24 images. LINE APNG and WeChat effect frame limits are not GIF requirements.

For a complete album, use `scripts/audit_wechat_album.py ALBUM --expected 24` (or the actual planned count). Set `--title` for subsequent series; `--partial` permits progress previews but is not final acceptance. It writes a portable gallery and checks GIF dimensions, loop, byte limit, duplicate content, transparent cover/icon and banner. The layout expects `gifs/*.gif`, `cover.png` (240 square), `icon.png` (50 square), and `banner.jpg` (750 x 400). Full-size originals stay preserved. A high-quality JPEG can fit the banner limit when its PNG is too large.

Different albums need genuinely distinct covers and chat icons. Reusing either caused two review rejections on 2026-10-09. Give each volume its own pose/composition and matching banner, appreciation guide and thank-you art; preserve accepted GIFs when repairing packaging. Run `scripts/audit_wechat_packaging.py` across volumes and visually review the 50-pixel icons. See [distinct packaging](references/distinct-album-packaging.md) for exports and same-work resubmission.

For a second series, preserve accepted identities while filling new everyday reply needs. A loose day-together arc can connect the set, but each sticker must work independently. Record the actual model profile and steps rather than equating a "better model" with better results. Preparing an album locally does not authorize submitting it; keep the first work and the unpublished successor separate.

## Browser upload and receipts

Reuse the user's specified authorized Chrome/CDP profile. Use available browser controls, or the installed `lalachan-xyq-browser-video` helper as a general CDP transport. Discover page IDs and observed controls rather than hard-coding a live account's identifiers.

1. Open `https://sticker.weixin.qq.com/`; user handles QR login if needed.
2. Choose 提交作品 -> 表情单品 for a pilot. Inspect the actual form.
3. Bring it to the front; attach the GIF with the real file input. Wait for remote preview and thumbnail, then fill 含义词 and relevant tags.
4. Verify the thumbnail/chat preview. Save a private screenshot and durable edit URL.
5. Save or submit according to the user's authorization. Report saved, submitted for review, approved, and live as distinct states; never retry a successful submission merely because approval is pending.
6. For 创建形象, inspect eligible works first. Do not associate unrelated old work. The observed form imposed six-month limits on changes to name/avatar/icon/description.

For albums choose 表情专辑 and 动态表情 instead of the single route. Upload sorted GIFs into one form, append only missing files when staging uploads, and verify remote order and meaning words. Banner, cover and icon have separate file inputs. Re-read checked values after each reactive form update. Use a name within eight Chinese characters, a short viewer-facing description, and the appropriate daily/cute classification. Confirm the complete count and thumbnails before one submission; retain the durable work URL and review status. Do not resubmit an already pending pilot single.

For an authorized compact update of a listed pack, use its existing Modify control
and inspect the monthly edit allowance. If exhausted, preserve the live listing
and prepared edition; do not unlist or duplicate it. A GIF-only replacement should
snapshot and verify all other metadata, packaging, price and appreciation after
reload. Submission success may coexist with `已上架` and `信息审核中`: the old
release is live while the new edition awaits review.

For a specifically requested free extension, select `免费` explicitly and retain
appreciation. The staging helper accepts metadata `price_mode: "free"`; its
existing paid default is unchanged. Verify both choices after saving. A draft
upload is not review submission.

A blank upload route after login can be a failed static-resource request. Inspect loading evidence; revisit the dashboard and reopen the same route before replacing the browser or asking for another login.

A new work ID alone does not prove a saved draft. GIF previews may remain local blobs until Save; verify complete local thumbnails first, then remote GIFs and all five packaging roles after reload, along with text, paid mode and appreciation. If login expires during Submit, recover the session and inspect that work's status before retrying. `stage_wechat_album.py` stages/saves empty drafts; `replace_wechat_draft_gifs.py` edits an explicitly identified existing draft. Neither submits review. See [series expansion and review](references/series-expansion-and-review.md) for the verified recovery sequence.

## Appreciation settings

The LALACHAN owner requests `接受赞赏` enabled by default for future sticker works wherever available, unless explicitly overridden. This is an owner preference, not consent to monetize another user's work. Before submission, complete the appreciation message, guide image and thank-you image, using approved series artwork when possible. Re-read the checked state and verify it persists on the saved work's settings page.

The appreciation and thank-you artwork can feature any of the four buddies; rotate characters to match the pack rather than always using Aya. Introductions name all participating buddies, including Zhuangzi the robot. Platform meaning words and lettering inside a GIF are separate: honor a trigger-only edit without rewriting or rerendering the accepted GIF.

On 2026-10-04 the album form accepted a 5-15-character message, a 750 x 560 guide image and a 750 x 750 thank-you image. A valid 240-square sticker GIF exceeded 500 KB after the platform enlarged it for appreciation. Reusing that sticker's PNG preview worked; pad the landscape guide instead of letting the platform crop ears or lettering. Inspect both uploaded previews. Keep the original animated album files unchanged.

For a pending work, inspect available editing first. Do not withdraw or create a duplicate to change this option without authorization. When the owner has withdrawn it for editing, complete and resubmit the same work once, then verify both review status and appreciation. Appreciation is distinct from a red-packet-cover distribution link; enabling it does not prove payout verification or platform approval.

## Paid Access

Paid access is different from appreciation. Check the current official paid guide and account eligibility before proposing it. The guide checked on 2026-10-04 required one published album and a separate application; it did not allow published free and paid albums to switch modes. Content-edit permission does not imply repricing permission. Promotional works have separate restrictions. An informational question is not authorization to submit identity/bank details, withdraw a pack, or change its price.

## Records

For Telegram, GIPHY and other distribution routes, read
[cross-platform stickers](references/cross-platform-stickers.md). Reuse approved
animation, verify current platform eligibility, preserve interrupted-send receipts
and report upload, review and live install/search states separately.

For a separate public sticker shop, read [multilingual storefronts](references/multilingual-storefront.md).
Keep the selected public edition separate from the owner's archived alternatives;
translate lettering from clean animations, and bind each purchase to all advertised
language ZIPs. Optional support pricing never changes those download rights.

For this owner's sticker series, keep the approved offline gallery design and export every volume to the configured Nutstore `Share/Stickers/Vol-NN` folder. Include original GIFs, portable HTML, a full-page CDP screenshot and one screenshot of each GIF. The bundled `scripts/snapshot_wechat_gallery.py` reuses an existing local-gallery tab, checks image loading and count, excludes account receipts, preserves timestamped captures and verifies copied hashes. The sync-folder location is local configuration, not a hard-coded public home path.

`build_sticker_library.py` provides a portable all-series overview. Clicking a GIF opens the embedded viewer; previous/next respects filters, and Close/Escape/browser Back restore the review position. Keep old assets and avoid periodic reloads during inspection. Album backlinks depend on destination depth; verify them after copying. Use `sticker_review_sheets.py` for phase/chat-size samples plus running-GIF review.

Use `--archive-root` to include preserved exports in separate historical and alternative views. Exact copied GIFs are indexed once, without deleting originals. Public preparation is opt-in with `public: true` and `--public-only` into a new empty destination; it never deploys. See [independent editions and gallery](references/independent-editions-gallery.md) for audit boundaries, portable exports and browser tests.

See [the album production runbook](references/album-production.md) for the full sequential workflow, resume rules, upload ordering and resource lessons.

Keep private upload handles, account screenshots, cookies, paths and generated artifacts outside public Git. A portable handoff should name input/output roles, dimensions, hashes, generation settings, actual review result and platform status. Copy chosen deliverables to the configured sync folder and compare hashes; distinguish copying from confirmed cloud synchronization.

Design reference: [LINE animation guide](https://creator.line.me/en/guideline/animationsticker/detail/) emphasizes readable first frames and everyday communication. Borrow the design principles, not its different export limits.
