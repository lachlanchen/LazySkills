---
name: wechat-sticker-production
description: Create and review a consistent WeChat sticker series, animate approved character references with LocalVideoGen, convert owned video into bounded GIFs, and upload singles or albums through an authorized WeChat Sticker Platform browser.
---

# WeChat Sticker Production

Use this for the WeChat Sticker Platform, not WeChat chat-message automation or social video publication.

## Design and review

Define a small series around common chat replies. Each sticker should work alone, while shared clothes, palette, character relationships, or a small daily-life arc connect the set. Prefer one or two clear subjects, a large expressive face, a simple backdrop, and one readable action. Learn from public sticker collections without copying their characters or assets.

For LALACHAN, inspect the canonical individual images first. Aya is the red panda in a navy sailor outfit; Lala is the black-and-white panda. Preserve the user's approved reference, including prior versions. Do not force every buddy or branded prop into every sticker.

Work one sticker at a time when requested: reference -> user/style acceptance -> local animation -> small-size/loop review -> upload. Planned stickers are not generated stickers. Later cute-angry interactions can form reply pairs such as 哼 / 给你 / 好吧 without becoming hurtful or requiring the full story to understand them.

The first still must already communicate the emotion. Inspect at 240 px and chat-like 120 px, with audio absent. Check character identity, limb count, expression, text, crop, motion, and three repeated loops. A smooth global image wobble is not a substitute for a character acting.

## Local animation

Discover the current LocalVideoGen API and its resource policy from the installed repository. Use its validated image upload and render API, keep the accepted reference as first frame, optionally as final frame for a loop, and save the job ID immediately. Submit once, monitor that same ID, download its observed output, and fully decode/sample it. Do not automatically regenerate or start a batch after a weak result.

Check RAM, swap, GPU and queue before rendering. Small output dimensions do not eliminate model-loading memory. Keep the normal resource gates; clean up only verified owned idle runtimes. Never close an active VM or another project's service just to fit a render. Stop the render services you launched when finished, while preserving a browser or image viewer needed for user review.

## GIF packaging

Bundled helper: `scripts/video_to_wechat_gif.py`. Requires Python 3.11+, Pillow, FFmpeg, and an explicitly supplied CJK font when text is used.

```bash
python3 scripts/video_to_wechat_gif.py INPUT.mp4 OUTPUT.gif \
  --duration 5.125 --speed 1.25 --fps 15 --label 哈哈 --font "$CJK_FONT"
```

It creates a GIF, preview PNG and provenance JSON without overwriting earlier versions. Recheck quality after palette/fps reduction. Flat backgrounds often look cleaner with no dithering; this is an aesthetic choice, not a universal rule. Keep the native source MP4, even though GIF carries no sound.

Read the current [WeChat official specifications](https://sticker.weixin.qq.com/cgi-bin/mmemoticon-bin/readtemplate?t=guide/index.html#/makingSpecifications#specifications_stickers). On 2026-10-04 a dynamic single used 240 x 240 GIF, looping, <=500 KB. This helper conservatively targets 500,000 bytes. The meaning word allowed four Chinese characters. Albums required 8-24 images. LINE APNG and WeChat effect frame limits are not GIF requirements.

## Browser upload and receipts

Reuse the user's specified authorized Chrome/CDP profile. Use available browser controls, or the installed `lalachan-xyq-browser-video` helper as a general CDP transport. Discover page IDs and observed controls rather than hard-coding a live account's identifiers.

1. Open `https://sticker.weixin.qq.com/`; user handles QR login if needed.
2. Choose 提交作品 -> 表情单品 for a pilot. Inspect the actual form.
3. Bring it to the front; attach the GIF with the real file input. Wait for remote preview and thumbnail, then fill 含义词 and relevant tags.
4. Verify the thumbnail/chat preview. Save a private screenshot and durable edit URL.
5. Save or submit according to the user's authorization. Report saved, submitted for review, approved, and live as distinct states; never retry a successful submission merely because approval is pending.
6. For 创建形象, inspect eligible works first. Do not associate unrelated old work. The observed form imposed six-month limits on changes to name/avatar/icon/description.

A blank upload route after login can be a failed static-resource request. Inspect loading evidence; revisit the dashboard and reopen the same route before replacing the browser or asking for another login.

## Records

Keep private upload handles, account screenshots, cookies, paths and generated artifacts outside public Git. A portable handoff should name input/output roles, dimensions, hashes, generation settings, actual review result and platform status. Copy chosen deliverables to the configured sync folder and compare hashes; distinguish copying from confirmed cloud synchronization.

Design reference: [LINE animation guide](https://creator.line.me/en/guideline/animationsticker/detail/) emphasizes readable first frames and everyday communication. Borrow the design principles, not its different export limits.
