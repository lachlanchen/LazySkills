# Animated Album Production

## Scope and visual direction

Complete the requested album, not only its first pilot. The current first series has 24 daily replies, Aya and Lala as leads, and Sasa and Zhuangzi as supporting characters. The approved tactile figurine style uses a white background, fixed clothing, large expressions, and one readable gesture per GIF. Render each action separately and retain its original reference and MP4.

The sequence suggests a day together without making any sticker depend on previous messages. A short reply trio such as `给你 / 哼 / 好吧` can also tell a miniature reconciliation story. Affectionate contact needs explicit ownership: whose paw touches which cheek, shoulder, or hand. A studio-floor contact keeps standing and jogging actions grounded.

## Reusable tools

- `scripts/render_wechat_sticker.py`: one approved reference, one local H3 render, durable receipt, resumable monitoring, decode check and GIF packaging.
- `scripts/video_to_wechat_gif.py`: bounded GIF export, optional accurately typeset CJK label, PNG thumbnail and provenance JSON.
- `scripts/audit_wechat_album.py`: dimensions, animation, infinite loop, byte limits, unique content, cover/icon transparency, banner size and portable gallery.
- `scripts/xyq_cdp_browser.py`: shared authorized Chrome/CDP transport for observed WeChat form controls and real file uploads.

Example paths below are local configuration variables, not public account identifiers:

```bash
python3 scripts/render_wechat_sticker.py "$SERIES/14-sasa-wait.json" --font "$CJK_FONT"
python3 scripts/audit_wechat_album.py "$SERIES/album" --partial
python3 scripts/audit_wechat_album.py "$SERIES/album" --expected 24
python3 -m unittest discover -s tests -p '*wechat*.py'
```

The still reference must be inspected before `reference_approved` is true. The JSON includes the label, seed, reference path relative to the spec, action, individually declared entities, anatomy and named contacts. Review each finished source and compressed GIF before copying it into `album/gifs/` and starting the next job.

## Resume without duplicate renders

The helper records an intent before submission and a receipt immediately after acknowledgement. The receipt binds the job to a SHA-256 fingerprint of its spec and reference. Re-running the same command resumes that ID; changed inputs cannot silently reuse it. An intent without a receipt is ambiguous and blocks another POST until the server job list is inspected.

An explicit HTTP 400 validation rejection before GPU allocation is different from a failed render. Preserve the rejection and request, correct the actual contract or ambiguous wording, and archive the rejected intent before submitting the corrected request. Never treat a timeout as proof that no render exists.

Observed LocalVideoGen validator false positives included `one hand` being interpreted as total anatomy, and `in place ... me` being interpreted as inserting a new person. Explicit right/left-hand wording and a separate sentence for jogging resolved these without disabling resource or anatomy validation. A bug report should include the original rejected prompt, not merely the workaround.

## Resource handling

Check available RAM, swap, GPU ownership and the queue. Run at most one H3 job at a time. This run used GPU 0; GPU 1 and the active Windows/macOS VMs remained untouched. Small 512-square output still requires large model-loading memory.

When the owner authorizes additional swap, add only a new verified file after checking free disk, permissions and existing swap. Record it privately; do not silently make it boot-persistent or disable memory gates. After completion stop only the exact render services this task started. Remove temporary swap only if enough real memory is available to migrate its used pages safely.

## Packaging and review

Current animated exports are 240 x 240, infinite-loop GIFs under a conservative 500,000-byte limit. Sources are about 5.125 seconds; 1.25x playback produces roughly 4.07-second stickers. The quiet source sound is not part of the GIF. A 15-fps, 256-color export is preferred when it fits; smaller palettes are checked for visual damage.

Review first, middle and final states, limb contacts, tail/ear crop, small-size legibility and the loop transition. The audit records a first/last-frame difference, not a subjective pass. Keep minor limitations in a separate review note. Preserve earlier versions and never regenerate automatically.

If only a label changes, export another GIF from the same source MP4. For example, `靠山` and `撑腰` share one animation. Keep both in `alternatives/`, but select only one for the numbered `gifs/` album; this is neither another model render nor an extra album slot.

Album assets: transparent 240-square cover, transparent 50-square icon, 750 x 400 banner. Keep the full-size originals. The PNG banner exceeded the upload limit in this run; a high-quality JPEG passed, and the PNG was retained. The form's current validation remains authoritative.

## One album, ordered uploads

1. Reuse the logged-in shared browser and open the dynamic album form once.
2. Upload sorted GIFs through its main file input. If uploading in stages, append only missing files; inspect the remote card count and order.
3. Fill every meaning word. Confirm the generated thumbnail expresses the action and is not blank.
4. Attach banner, cover and icon to their observed distinct inputs. Wait for upload previews to finish.
5. Fill the short title, description, copyright and appropriate classification. Check selected controls after reactive updates; several rapid clicks can otherwise leave an earlier selection unset.
6. Audit all 24 files and capture the full form before submitting once.
7. Record the returned work URL and dashboard status. Saved draft, pending review and live are different outcomes. A pending pilot single should not be resubmitted.

Creating a character collection requires eligible approved works on the observed platform. Do not attach an unrelated old word-card album just to complete that form. Wait until the new work becomes eligible.

## Deliverables and privacy

Copy the complete album, gallery, original references, source MP4s and review records to the configured Nutstore share. Compare SHA-256 hashes; distinguish local copy verification from cloud acknowledgement. Keep job IDs, account screenshots, runtime endpoints, source paths and generated assets in ignored/private storage. Commit only portable scripts, tests, design notes and reusable workflow documentation.
