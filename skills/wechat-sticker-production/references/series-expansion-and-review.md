# Sticker Series Expansion And Review

## Latest Owner Correction: Unique Animations

The owner rejected cross-pack animation reuse after reviewing the galleries.
This supersedes the reuse choices documented below: every selected formal GIF
needs its own distinct animation. New lettering, language, crop or compression
does not count. Audit native provenance across selected editions with
`audit_wechat_animation_reuse.py`, then visually compare actions. Exclude archived
versions and requested text revisions of the same sticker from the formal set.
Do not upload a pack whose selected animation is already used in another pack.
The first audit found 54 reused entries across the six newer packs; a passed
packaging hash audit had not detected this. Preserve originals and prepare
independent replacements. Obtain authorization before withdrawing pending works.

For the phonetic pack, keep normal Chinese platform meaning/trigger words; only
the lettering burned into the GIF is a playful Chinese transliteration.

The requested extension is 16 entries. Four additions separate displayed jokes
from useful search words:

| GIF lettering | Japanese source (internal reference) | Chinese meaning word |
| --- | --- | --- |
| 阿姨洗铁路 | あいしてる | 我爱你 |
| 私密马赛 | すみません | 不好意思 |
| 干巴爹 | がんばって | 加油 |
| 呆胶布 | だいじょうぶ | 没关系 |

Use distinct actions for these: shy love-letter offering, a small apologetic
gesture, energetic encouragement, and reassuring care. They are playful
transliterations, not language-learning pronunciation guides. These are planned
additions until their own references, animation receipts and reviews exist.

## Decisions From The October 2026 Run

- Preserve every generated variant, including incorrect outputs, native MP4s,
  references, GIFs and generation receipts. A replacement lives in a new folder.
- The owner selected the edge layout for formal uploads. Start at 1 px padding,
  then reserve only the space needed to keep movement and lettering readable.
- Keep cute outlined text around the action. Shorten a cumbersome caption before
  shrinking the character. For example, `躺会儿` fit more naturally than a longer
  sentence on the reclining pose.
- Existing review replacements and new drafts have separate authorization.
  Volumes 2 and 3 were replaced with edge editions and resubmitted on their same
  work IDs. Five new series were saved as drafts for owner selection; the owner
  subsequently authorized Cantonese, sports and research review submission.
  Authorization and the platform's verified submission state are separate.
- The five drafts contain 12 stickers each: daily supplement, Japanese daily,
  Cantonese daily, sports/rest, and research life. They combine newly generated
  actions with explicitly selected existing animations. They are not 60 newly
  rendered clips. Cross-series action reuse remains a review consideration.
- All five drafts were reopened to verify names, order, count, paid mode and
  appreciation. Account identifiers and screenshots remain private.

## Design Research

Chat usefulness comes before a complicated scene. Give each sticker one response
intent, a readable first frame and a recognizable gesture. Our interpretation is
that a loose shared day can connect an album without making a single reply depend
on seeing the entire album. This is a design hypothesis, not a promise of viral
distribution or measured sales.

The [CAS research-life sticker collection](https://www.cas.cn/newmedia/weixin/202111/t20211101_4811814.shtml)
is a relevant original Chinese example of scientific-work humor. The
[HIT Shenzhen account of conversational sticker retrieval research](https://hlt.hitsz.edu.cn/info/1001/1593.htm)
emphasizes conversational context and intent. These informed topic selection, not
copying another collection's artwork, captions or character design.

Research-life sequence: doing experiments, checking data, writing fatigue,
revision, acceptance, rejection, thinking again, a break, an idea, encouragement,
and finally finishing. Microscope and pipette gestures make the laboratory setting
concrete. Generic journal aspirations such as `冲顶刊` avoid implying Nature or
Science endorsement. Break/drink reactions are outside active bench work.

Sports sequence: start, tiny weight with exaggerated effort, one more curl,
ping-pong, a snack, skipping, sweat, water, rest, dinner, more rest, tomorrow.
The contrast between earnest exercise and comfortable recovery supplies humor
without mocking bodies or promising health outcomes.

## Language Review

The initial Japanese-script edition remains archived. The owner's later choice
is a **Chinese phonetic joke edition**, called `空耳小日常`: 空你七哇、哦呀斯密、
哦哈哟、他大姨妈、哦卡诶里、哦伊西、卡拉伊、伊伊尼欧伊、内木伊、
一大个麻薯、姨爹拉沙姨、阿里嘎多. These are playful approximations, not accurate
pronunciation tuition. Keep ordinary Chinese meaning words for platform search.
The initial text-only conversion preserved existing native animations; the later
cross-pack uniqueness correction now requires independent replacements where an
animation is selected elsewhere. This is an owner-specific content choice, not
evidence of a universal platform ban on Japanese.

[Miyakonojo City's multilingual leaflet](https://www.city.miyakonojo.miyazaki.jp/uploaded/attachment/4618.pdf)
uses Chinese approximations for basic greetings. This
[creator's Chinese-Japanese meme discussion](https://www.bilibili.com/video/BV1T8iUY5EgZ/)
illustrates the playful context. For actual coming/going meanings, consult
[Coto Academy's explanation](https://cotoacademy.com/ja/ittekimasu/).
Choose gestures that fit the reply, especially returning home versus seeing
someone off. Original Japanese lettering used licensed
[Zen Maru Gothic](https://github.com/google/fonts/tree/main/ofl/zenmarugothic).

Cantonese distinguishes `唔該` (help/service, or please) from `多謝` (thanks,
including gifts). See [CUHK Cantonese Express](https://www.ilc.cuhk.edu.hk/workshop/Chinese/Cantonese/CantoneseExpress/files/compare/Compare01_w.pdf).
The selected set also includes 早晨、唔使客氣、食飯未、好味、好攰、等陣、
冇問題、加油、恭喜、得閒飲茶. A CJK Hong Kong font with complete glyph coverage
replaced the rounded Chinese font where characters were missing. Prefer correct
glyphs to a stylistically similar missing-glyph box; keep the font license locally.

## Production Tools

1. Built-in image generation: pass inspected canonical character references;
   generate a clear first pose on white, and save the selected PNG in the project.
2. `render_wechat_sticker.py`: one local H3 job per inspected reference, receipt
   immediately saved, same-job resume, no automatic paid or local rerender.
   This run used 512-square, five-second `quality_int8_offload` jobs.
3. `export_sticker_selection.py`: a local JSON selection of `id`, `label`, and
   relative `source`; postprocess chosen native clips into a new album folder.
   Optional `sizes`, `padding`, `center`, and `vertical` adjust crowded captions.
4. `compact_wechat_sticker.py`: one motion-union crop, proportional scaling,
   caption placement, encoded-byte checks and source/output hashes. Optional
   Gifsicle `--lossy 20` is bounded and recorded; it is not lossless.
5. `sticker_review_sheets.py`: sample five phases plus chat-size previews.
   Review the running GIF too; sheets alone cannot prove motion quality.
6. `package_wechat_artwork.py`: unique cover, icon, banner and appreciation art;
   copies selected GIFs byte-for-byte. `audit_wechat_packaging.py` checks all packs
   for repeated packaging. Hash checks do not replace visual similarity review.
7. `stage_wechat_album.py`: fill an observed empty authorized form and optionally
   save a draft. It has no review-submit action. Reopen the same work to verify.
   `replace_wechat_draft_gifs.py` replaces an explicitly selected existing draft,
   guarded by work ID, old title and count; it saves but never submits review.
8. `audit_wechat_album.py`, `build_sticker_library.py`, and
   `snapshot_wechat_gallery.py`: portable galleries, artwork-only copies, full-page
   and per-GIF screenshots, local copied-file hash verification.

```bash
python scripts/export_sticker_selection.py "$SELECTION" "$REVIEW_ALBUM" \
  --font "$FONT" --gifsicle "$GIFSICLE" --lossy 20
python scripts/sticker_review_sheets.py "$REVIEW_ALBUM/gifs" "$NEW_REVIEW_SHEETS"
python scripts/audit_wechat_album.py "$ALBUM" --expected 12 --title "$TITLE" \
  --labels-file "$SELECTION" --library-href ../All-Stickers/index.html
python scripts/build_sticker_library.py "$LOCAL_LIBRARY_CONFIG" "$ALL_STICKERS"
python scripts/snapshot_wechat_gallery.py "$ALBUM" "$SYNC_ALBUM" \
  --cdp-url "$CDP_URL" --page-id "$EXISTING_GALLERY_TAB"
```

The selection exporter receives the **album root**, not its `gifs` subdirectory.
Choose the relative library link for the final directory depth. When a sync copy
has a shallower layout, rebuild only its HTML/audit with the corrected backlink;
the copied GIF bytes stay unchanged. Local sync-folder presence is not a cloud
acknowledgement.

## Lessons And Recovery

- A model preflight rejected two contacts that shared `bench:top`. Give the hand
  and microscope separate meaningful contact endpoints. Archive the rejected
  intent/request and correct the contract; no render occurred on that HTTP 400.
- Another parser read a number of pencil strokes as a number of pencils. Simplify
  the action wording while retaining the true prop inventory. Keep guards enabled.
- Seated/reclining characters need explicit seat contacts. The helper now accepts
  declared supports before adding a standing-floor fallback.
- The authorized redo of `客气啦` still introduced a toy car. Both outputs remain
  in the comparison area. The daily draft uses a separate already-accepted bow.
  The owner later explicitly liked BOTH car variants; they now seed a separate
  visiting-friends draft, `小车开到你家`, with `我走啦` and `拜拜`. Preserve the
  original deviation record while recording the owner's new creative selection.
- Rename the daily supplement `闪光的日常`, per the owner's latest choice.
- An expired login after Submit is not success evidence. Preserve the work ID,
  open login in the existing browser, request the owner's scan, and continue local
  work. After login, inspect the same work before deciding whether to retry.
- `参数错误` can occur after a new platform work ID appears. Preserve that ID;
  inspect the same form. A one-time same-work save or an explicit empty-draft
  repair is different from creating another work. A `保存成功` toast plus reloaded
  field/image/settings checks is required before reporting a saved draft.
- Packaging uploads must resolve to actual remote previews at the expected
  dimensions. A placeholder, local blob or created ID is not persistence proof.
- GIF previews can remain local blobs until Save, unlike packaging previews.
  Check complete local thumbnails before saving, then remote GIFs after reload.
  Replacing GIFs can leave packaging missing: verify all five art roles again
  after saving, not just the new GIF count. The corrected replacement helper's
  individual recovery steps were exercised on the same draft; do not rerun a
  completed edit merely to test the wrapper end to end.
- A Submit timeout can occur after the server accepted the work. In this run,
  research was already pending review when login recovered. Verify its durable
  setting page and avoid submitting twice.
- The platform can reject similar covers/icons even when GIFs differ. Each new
  pack has a genuinely different composition, not merely a changed title.

## Gallery Interaction And Tests

Click a GIF to open the inline viewer. Previous/next follows the filtered set.
Close, Escape and browser Back return to the same filter, search and scroll
position. Series names filter the overview; album pages include a library link.
The viewer is embedded in the HTML and works offline. It replaces disruptive
periodic refresh while someone is inspecting a sticker.

```bash
python -m unittest discover -s tests -p 'test_*.py'
PLAYWRIGHT_MODULE="$EXISTING_PLAYWRIGHT_MODULE" \
  node tests/sticker_gallery_browser.cjs "$ALL_STICKERS/index.html" "$QA_DIR"
```

The October review tested desktop and 375-pixel mobile layouts, filtering,
open/close, navigation, browser Back and Escape. Native files remain separate
from public reusable scripts. Stop only owned idle render services after the
queue drains; preserve the shared review browser and active VMs.
