# Immersive product walkthroughs

Use for a fuller app film, real two-account exchanges, or a request to carry the
quality of an accepted short into a longer demonstration. The aim is to make the
viewer understand what they could do, not to enumerate navigation labels.

## Plan from the actual app

Capture a small successful journey before writing the final dialogue. For a
messaging app, discovery → assistant draft → friend list → chat → receipt is a
useful example, not a mandatory order for every product. Name the human reason
for each action. A music app should let its output be heard; a reader should
show a passage becoming understandable. Do not reuse unrelated dialogue merely
because the earlier performance was good.

Read the current release/handoff and inspect the real UI. Prefer a ready native
device/simulator when it materially improves the demonstration. If it requires
disrupting another project or a substantial setup, use the owner-permitted PWA
and label the capture honestly. A store link is not proof of a store installation.
Do not change an app, its access rules or store release just to manufacture footage.

Write a compact shot contract: actual action, visible result, speaking character,
approximate duration, and which pixels must come from the app. Estimate speech
at ordinary pace and leave space to read and react. A 15-second scene does not
reliably hold a feature list plus multiple long sentences. Choose the number of
scenes from the requested coverage and resource budget, not a universal length.

## Two-account demonstration

- Verify the account on each side and the exact recipient before sending. Use
  separate authenticated browser contexts or qualified native sessions; two tabs
  sharing one origin's session can silently become the same account.
- Login before recording. Reuse a protected credential file with minimal access;
  never put credentials in prompts, screenshots, captions, scripts or this skill.
- Use a benign, task-relevant message the owner has authorized. Record the send
  intent, click once, then locate that same text/identity on the receiving side.
  A spinner or sender bubble alone does not establish receipt. Reconcile ambiguous
  results instead of sending a duplicate.
- Keep UI actions visible. Do not replace an inconvenient chat flow with hidden
  database/API writes or synthetic messages. Additional public posts, invitations,
  friend requests or unrelated conversations need their own task authority.
- Respect the owner's chosen presentation of their avatars and names; avoid
  unnecessary mosaic. Inspect for actual secrets and unrelated third-party data.
  Preserve original settings, drafts and conversations, and restore scoped demo
  changes when appropriate. Never delete existing material as cleanup.

## Make the action readable and alive

Start with an action or recognizable question, not a slow logo reveal. Let the
viewer see a useful result early. Show navigation briefly enough to establish
where the action happens; spend more time on the message, passage or output.

Record real transitions when demonstrating how to use the app. Stills can give
reading time or bridge an edit, but a slideshow must not be described as a full
interaction recording. Keep header, composer or other orientation cues where
they matter. Use a motivated crop/push-in on the actual result; avoid constant
zooming, mouse wandering and tiny two-phone layouts on a portrait screen. A clean
cut from sender to recipient is often clearer than shrinking both screens.

The characters should have a reason to look, ask, point or react. Keep phone and
hand ownership simple. Use a short question, a helpful response and a believable
reaction, rather than two mascots reading marketing copy. Give non-speakers small
gaze/posture reactions without competing with the app. Ask for warm ordinary
speech and natural pauses; do not claim voice matching from a text prompt.

Generate performance and native dialogue together where this produced the
accepted style. Use current LocalVideoGen parser/admission rules. Model outputs
may add words, invent software or drift in speaker assignment even when the
built-in expected-dialogue score passes. Inspect each source, not just its score.

When removing unwanted speech, cut picture and sound together at checked quiet
boundaries. Preserve meaningful words and the original speed. A brief silent
reading bridge may be hidden entirely under opaque real UI, but never expose a
frozen speaking face or use loud music to conceal broken dialogue. If an edit
cannot remain coherent, report the specific defect and choose a bounded repair;
do not start an unlimited regeneration loop.

## Conversation and light music

Keep the native performance as the dialogue/scene-audio master. Use an owned or
licensed, unobtrusive instrumental when requested; avoid lyrics competing with
speech. Native generated ambience may already be enough. An app's demonstrated
audio should remain audible, not be drowned out by a separate score.

Mix for intelligibility at ordinary phone volume, with restrained fades/ducking
and measured clipping/loudness checks. A successful numeric peak or ASR score
does not establish a pleasant listening balance. Do not bake in one music gain
or loudness target as universally correct. Avoid unnatural global speed changes.

If the owner asks for both versions, export the same reviewed picture timeline
with (a) a light music bed and (b) the native dialogue/scene audio without that
added bed. Preserve dialogue synchronization. Reuse the encoded video stream
where possible and compare packet or decoded-frame hashes; only the audio mix
should differ. Do not call the native version absolutely music-free unless it
has been checked for incidental model-generated music.

## Review the film, not just the render

1. **Story:** can a new viewer state the problem, the actual action and the small
   payoff? Does each included app area contribute to the requested walkthrough?
2. **Product:** capture the real interface and result; verify sender/recipient
   continuity, current feature access and truthful platform claims.
3. **Speech:** transcribe the retained words in their actual language; check
   extras as well as omissions. Review voice naturalness, speaker identity,
   lip timing and music balance separately. If direct listening is unavailable,
   state that limit privately and deliver for review, not as listening-approved.
4. **Picture:** inspect the complete sequence and closer transition frames for
   invented UI, exposed frozen boundaries, cropped controls, unreadable text and
   discontinuous hands/phones. Review at phone-sized display, not only a giant
   contact sheet. Use consistent icon/title and restrained real store artwork.
5. **Delivery:** full decode/probe, corrected subtitle source, metadata draft,
   source/edit manifest, exact file hashes and both requested audio variants.
   Label upscaling honestly and keep heavyweight/private evidence outside Git.

Follow the main skill's publication subtitle defaults; a clean review master is
not permission to publish without them. Preparation is not publication. Retire
only exact owned render/capture processes after verified collection, preserving
accepted assets and other projects' work. Slow full-quality model computation
is not a reason to kill shared processes or discard a nearly finished render.
