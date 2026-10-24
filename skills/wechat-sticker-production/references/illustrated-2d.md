# Illustrated 2D Stickers

Use the approved versioned four-buddy library at
`LALACHAN/assets/characters/2d/v1/` for this owner's 2D work. The existing 3D
figurine references remain a separate style. The sheet is the style authority;
individual transparent PNGs identify Lala, Aya, Sasa and Zhuangzi.

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
