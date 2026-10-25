# Illustrated 2D Stickers

Use the approved versioned four-buddy library at
`LALACHAN/assets/characters/2d/v1/` for this owner's 2D work. Use `lala.png`,
`aya.png`, `sasa.png` and `zhuangzi.png` as individual character references.
The sheet is the style authority, including its approved bottom-row reactions.
For normal 3D work, use root `raraxia.jpeg`, `ayachan.png`, `sasakun.jpeg` and
`LazyingArtRobot.png` instead. The complete current-use guide is
`LALACHAN/references/characters/four-buddy-reference-guide.md`.

`scripts/export_2d_character_library.py OUTPUT --cast aya lala` in LALACHAN
verifies hashes and creates a numbered cast with a path-free upload-order note.
Export only the characters needed. This is useful for XYQ attachments and local
reference-frame preparation; it does not submit a paid render.

For animated stickers, generate a reviewed first pose that already reads at chat
size, then use `visual_style: "illustrated_2d"` with the local renderer. The
default renderer is still 3D, so the explicit style field matters. Preserve warm
outlines, character colors and clothing while animating eyes, mouth and joints.
A static illustration, text bounce or global rotation is not character animation.

Describe a small anticipation, one clear action and a reaction hold. Pair actions
such as hugging or carrying need visible hands and stable support. Match the
physical contract to the actual first frame. Anatomical phrases like "one hand"
can be misread by a count validator: name left/right limbs when relevant, and
fix the prompt rather than bypassing that guard.

The local workflow separates native animation from caption/encoding work:

1. `prepare_2d_sticker_specs.py` creates finite specs from a plan; approve only
   references actually inspected.
2. `render_sticker_batch.py` runs an explicit approved list sequentially and
   stops on failure. Resume the same receipts after interruption.
3. `package_2d_stickers.py` chooses text placement using the whole motion union
   and exports small looping GIFs, preserving native video.
4. `audit_2d_stickers.py` checks GIF frames, loop, bytes, and distinct native
   hashes/job IDs. Review actual motion as well; technical uniqueness does not
   prove good acting.
5. `build_2d_sticker_review.py` includes completed GIFs only, with original-video
   links and the reusable character library. Keep previews separate from store
   submission and public deployment.

The first 2D study used public Reels to learn readable poses, ordinary props,
pause timing and affectionate reversals. New assets use the owner's characters
and original animation, not third-party footage or full copied scripts.

## Transparent Release

Review alpha separately from the accepted acting. Semantic matting can remove
white robot panels, cream clothes, pale eyebrows and eye glints. Compare source
and cutout on dark and saturated backgrounds across motion, including the frame
with the largest repair. Enclosed background gaps must remain transparent.

LALACHAN's `restore_2d_solid_regions.py` and `patch_2d_interior_alpha.py` offer
supervised enclosed-component repairs for this flat-art palette. Explicit
regions and an optional warm/cool chroma gate protect selected interiors while
retaining the existing soft outer edge. They are not a generally validated
background-removal model. Inspect neutral details and open outlines separately.
Keep every candidate; bind approval to hashes with `review_sticker_catalog.py`.

Use `letter_2d_matte_stickers.py` for the reviewed alpha masters: rounded white
type with dark outline, restrained bounce/tilt, one motion-union crop, small
safety inset and per-sticker placement around the acting. Review at 240 and
120 px. The exporter checks clipping and overlap, but taste still needs visual
review. Preserve soft-alpha APNGs for LINE conversion and verify the encoded
GIF/APNG rather than trusting the source preview. Never white-key them again.

Use separate covers, banners, icons and appreciation art for paired packs.
Check destination-specific free/paid options and price approval. For the
October 24 pair the owner approved LINE's lowest paid tier for both; the first
pack remains free on WeChat and AYA. This is not permission to reprice old packs.

The three-language gallery supports light/dark/pink backgrounds. Sync selected
artwork and review screenshots to Nutstore, keeping private platform receipts
outside artwork bundles. AYA and WeSticker should show the same public edition;
do not touch users' private packs or activate unqualified payment offers.

For an interrupted batch upload, compare the displayed thumbnails against the
selected GIF frames before appending anything. The platform may make a PNG
thumbnail, so its byte hash is not the GIF hash. Append only the missing item,
map meaning words to the resulting visible order, and verify the saved draft
after reload. Preserve the work ID and submit once; a successful result page
and a dashboard row awaiting review are separate useful receipts.
