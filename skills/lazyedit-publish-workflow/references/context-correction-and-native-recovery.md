# Context correction and native recovery

Use the creator's explicitly confirmed spoken lines to resolve conflicting ASR.
Scene descriptions, scripts and story background are reference, not evidence
that a line was spoken. Do not turn visible actions into dialogue or keep an
ASR hallucination merely because it forms a fluent sentence.

Use the normal correction API with the clarified context. A rejected ASR cue
keeps its original timestamps and empty text in the polished audit transcript;
translation skips that empty cue. Compare original and polished timing, then
verify every nonempty translated cue corresponds to retained speech. Check a
silence frame as well as a speech frame. Avoid manual generated-file replacement.

For Korean, choose a natural translation first. Zero Hanja is valid for native
words; restore confidently identified Sino-Korean roots without forcing extra
ones. The restored root uses exact Hangul ruby, while native endings stay visible
with romanization. For example, 감사 / 感謝 / 감사 followed by 합니다 / 합니다 /
hamnida. A suffix must not disappear into the root's ruby or remain inside a mixed
Hanja/Hangul display word. Shared dictionary-backed formatting and bounded model
review handle this; do not patch individual rendered subtitles.

If polishing changes a wrongly tagged English cue into Han-only Chinese, a
native-text lock must not force that cue to stay Chinese in the English row.
Fix stale-tag handling in the shared translator; preserve genuine native speech.

Native Studio's authenticated composer, plan and submit endpoints use the normal
pipeline. Save the intent/idempotency key before submission, then follow that job.
A known local preparation failure is retryable only when the completed failed
row proves there was no ZIP or remote dispatch. An ambiguous, active or dispatched
job requires receipt checks, never a new whole-job submission. Reuse the same
verified run for publication after correction.

Read account-scoped capabilities and publication scopes. Repair an older owner
adapter's response compatibility without promoting unrelated worker builds or
giving private members/reviewers the personal Pi. Avoid editing autoreloaded
Python modules during a render; activate necessary fixes at a safe boundary.

Keep metadata grounded in the corrected speech and observed scene. Output
language does not imply filming location. Preserve concise viewer-facing text.
