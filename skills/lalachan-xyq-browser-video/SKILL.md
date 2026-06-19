---
name: lalachan-xyq-browser-video
description: Use when generating, preparing, monitoring, downloading, or publishing LALACHAN Xiaoyunque videos through a logged-in Chrome/CDP web UI, especially requests mentioning Lala Xia, Aya Chan, Sasa Kun, Xiaoyunque, XYQ, Seedance, 沉浸式短片, Agent 模式, reference images, reference video, Nutstore copying, low-credit generation, or avoiding the Xiaoyunque API.
---

# LALACHAN Xiaoyunque Browser Video

## Core Rule

Prefer the logged-in Xiaoyunque browser UI over the Xiaoyunque API unless the user explicitly asks for API usage. Validate visible page state before submitting: mode, model, duration, ratio, prompt, attachments, and credit estimate.

Use the bundled scripts first:

```text
scripts/xyq_cdp_browser.py
scripts/xyq_chrome/watch_thread_dom_download.py
scripts/xyq_chrome/launch_chrome.sh
```

Load detailed references only when needed:

```text
references/xyq-browser-video-generation-skill.md
references/uploaded-images-no-path-workflow.md
references/xyq-browser-automation-workflow.md
references/smooth-video-generation-runbook.md
references/continue-confirm-download-runbook.md
references/30s-agent-workflow.md
references/words-card-30s-default.md
```

## LALACHAN Defaults

Default uploaded image order in the LALACHAN project:

```text
words-card.jpg
LazyingArtRobot.png
display.png
patchwork-leather-notebook-luxury-clean-v2.png
raraxia.jpeg
ayachan.png
sasakun.jpeg
Trio.png
```

Prompt labels after upload:

- 图1: words card / 小白屏学习卡.
- 图2: `LazyingArtRobot.png`, robot `庄子`; keep the LazyingArt logo on chest.
- 图3: LightMind AI glasses.
- 图4: handmade patchwork notebook.
- 图5: `raraxia.jpeg`, individual 啦啦侠 / Rara Xia reference.
- 图6: `ayachan.png`, individual 阿芽酱 / Aya Chan reference.
- 图7: `sasakun.jpeg`, individual 飒飒君 / Sasa Kun reference.
- 图8: `Trio.png`, three-character group identity reference.

Characters:

- `啦啦侠 / Lala Xia`: giant panda from `Trio.png`.
- `阿芽酱 / Aya Chan`: red panda from `Trio.png`.
- `飒飒君 / Sasa Kun`: boy from `Trio.png`.
- `words-card.jpg`: words card / 小白屏学习卡 style reference.
- `LazyingArtRobot.png`: robot `庄子`; preserve the LazyingArt chest logo.
- `display.png`: LightMind AI glasses.
- `patchwork-leather-notebook-luxury-clean-v2.png`: handmade patchwork notebook/tool prop.
- `raraxia.jpeg`: individual 啦啦侠 / Rara Xia reference.
- `ayachan.png`: individual 阿芽酱 / Aya Chan reference.
- `sasakun.jpeg`: individual 飒飒君 / Sasa Kun reference.

Words-card rule:

- Treat `图1` as the visual style reference for the physical learning card.
- Use `/home/lachlan/ProjectsLFS/LALACHAN/words-card.jpg` as the default words-card reference image when uploading directly. Use a pre-generated card image only when a fresh card has already been made for the specific episode.
- For every new video, create a fresh story-relevant word card; do not reuse the previous word unless the user asks.
- The card content must include English, Japanese, and Japanese furigana. Add a short Chinese meaning when useful.
- Use the successful in-scene prompt pattern by default: `图1 是小白屏学习卡风格参考，可作为场景边缘/桌面/道具架上的小道具，卡片内容是 English: WORD；Japanese: 日本語；Furigana: ふりがな；中文：中文含义。它只是场景里的真实道具，不是字幕。`
- Choose a word that matches the episode theme, for example battle/courage scenes can use `courage / 勇気 / ゆうき / 勇气`.
- Two valid methods are allowed:
  - Pre-generate a new words-card image first with AgInTi/image generation, then upload that generated card as `图1`.
  - Upload the existing words-card as a style/example reference, then give Xiaoyunque the exact English/Japanese/furigana content and make it responsible for rendering the new card in the scene.
- Use either method, or both, as long as the final video has the fresh words card. Prefer pre-generation when text accuracy matters.
- The card is a real prop in the scene, not a subtitle overlay.

Story writing rule:

- Write stories in natural, understandable Chinese first. The viewer should understand the action, joke, and emotion without reading production notes.
- Keep one clear cause-and-effect chain per short video: problem, response, twist, payoff.
- Dialogue should sound like friends talking. Avoid pseudo-code, abstract slogans, machine-like phrases, over-explained lore, and strange translated wording.
- Use simple concrete nouns and actions. Prefer "培养皿在显微镜下慢慢亮起来" over vague phrases like "生命数据完成同步".
- If a concept is educational or technical, show it through a visible action and one plain sentence, not a lecture.
- For lab scenes, keep the lab clean and believable: gloves, sterile bench, incubator, microscope, pipette, petri dish, and careful movement. Dance can happen as small safe steps, shoulder moves, or rhythm while working, not reckless lab behavior.
- Before turning a new story into a Xiaoyunque prompt, run a critic pass using `lalachan-story-critic` when available. Fix exact awkward lines first, then write the final prompt.

Never paste local filesystem paths into the Xiaoyunque prompt. Paths are only
for the browser file upload command. The prompt should say `图1` through `图8`
and explicitly ask not to draw file names or paths into the video.

Always upload the actual reference image files before generation. Do not treat
typed local paths, pasted filenames, or prompt-only image descriptions as a
substitute for upload. Before any paid submit, verify visible attachment
evidence for every required reference image. If image upload fails or cannot be
proved, stop and fix/report the blocker instead of submitting.

Default video setup:

```text
Mode: 沉浸式短片 by default for normal LALACHAN video generation
Model: Seedance 2.0 Fast by default for LALACHAN videos
Duration target: 15s by default
Ratio: 4:3 unless the user requests otherwise
Prompt language: mainly Chinese
Always include: 不要字幕，不要生成任何字幕、说明文字、下三分之一文字或画面文字。
```

For default work, target `15秒` and prefer `沉浸式短片` with non-VIP
`Seedance 2.0 Fast`. Use `创作 Agent` / integrated-agent only when the user asks
for a longer video, when the current active thread is already an Agent thread,
or when short-film controls cannot satisfy the task. If a generation fails,
continue in the same current thread by sending a short corrective message; do
not start a new session or new thread just to retry unless the current thread is
unusable and the user accepts that cost/risk.

Use `30秒` or longer only when the user explicitly asks for it.

## Credit-Budget Rule

- Default to `Seedance 2.0 Fast` for LALACHAN video generation.
- Inspect the model dropdown and avoid any option containing `VIP`.
- Do not choose `Seedance 2.0 Mini` by default; the user found Mini expensive. Use Mini only when the user explicitly requests Mini or accepts it after seeing the cost.
- Use normal `Seedance 2.0` only when the user explicitly asks for non-Fast or higher quality over credit savings.
- If the user asks for cheapest, inspect the visible point cost first and report the tradeoff; do not silently switch away from requested/default Fast.
- Do not continue an `智能长视频` / Agent render if the final video cost exceeds the user's budget; switch to short-video workflow or report the blocker.
- For `4:3`, verify the opened ratio menu checkmark or screenshot because the compact toolbar may still show only `比例`.
- Never waste credits on avoidable retries: do not click `生成视频`, `提交`, or
  any paid action twice unless the page proves the first attempt failed without
  charging. If points drop or the task shows queued/running, monitor only.

## Browser Workflow

1. Attach to an existing logged-in Chrome CDP endpoint, usually `http://127.0.0.1:9222` or another active port:

```bash
scripts/xyq_cdp_browser.py --cdp-url http://127.0.0.1:9222 list-pages
```

2. Bring the Xiaoyunque page forward and inspect visible controls:

```bash
scripts/xyq_cdp_browser.py --cdp-url http://127.0.0.1:9222 bring-to-front PAGE_ID
scripts/xyq_cdp_browser.py --cdp-url http://127.0.0.1:9222 visible PAGE_ID
```

3. Select mode/model/duration/ratio by browser UI. Do not submit until the page proves the requested mode, non-VIP model, duration, ratio, and point cost.

4. Upload and verify reference images:

```bash
scripts/xyq_cdp_browser.py --cdp-url http://127.0.0.1:9222 upload-images-verify PAGE_ID \
  words-card.jpg \
  LazyingArtRobot.png display.png patchwork-leather-notebook-luxury-clean-v2.png \
  raraxia.jpeg ayachan.png sasakun.jpeg Trio.png \
  --timeout 180 \
  --screenshot outputs/xyq-run/after-upload.png
```

5. Fill the saved prompt:

```bash
scripts/xyq_cdp_browser.py --cdp-url http://127.0.0.1:9222 type-prompt PAGE_ID references/prompts/example.md --wait 2
```

6. If the submit button stays disabled, inspect upload item classes. Wait until every uploaded file item is `success`; a single `uploading` reference blocks submission.

7. If the current thread pauses, fails, or needs a correction, first send a
   short message in the same thread. Avoid new sessions because they can waste
   credits and confuse the user. Use `创作` / new-session only when the current
   thread is truly unusable or the user explicitly asks.

8. Submit only when the user asked for generation and the pre-submit contract is satisfied.

## Agent Confirmation Pauses

Long-video / Agent workflows may stop after storyboard or reference-material
creation and ask the user to confirm before generating video. If the page asks
for continuation, reply in the same thread with a short message such as
`继续生成视频。`; do not start a new generation. Use `type-prompt` or real browser
keystrokes so the chat input enables the send button.

```bash
scripts/xyq_cdp_browser.py type-prompt PAGE_ID outputs/xyq-run/continue.md --wait 0.3
scripts/xyq_cdp_browser.py click PAGE_ID SEND_BUTTON_X SEND_BUTTON_Y
```

## Watch, Download, Copy

Monitor the submitted thread through the browser page:

```bash
scripts/xyq_chrome/watch_thread_dom_download.py \
  --cdp-url http://127.0.0.1:9222 \
  --page-id PAGE_ID \
  --thread-url "THREAD_URL" \
  --output-dir outputs/xyq-run \
  --filename result_30s.mp4 \
  --copy-to Videos \
  --copy-to "/home/lachlan/Nutstore Files/AutoPublish/AutoPublish"
```

Protected `everphoto` URLs may fail from unauthenticated direct HTTP. First test browser-context fetch with `--await-promise`; if it returns `200 video/mp4`, pull the active `video.currentSrc` from the page and download with browser-like `Referer` and `User-Agent` headers.
The bundled watcher can now use this same browser-context path by triggering an
in-page blob download and copying the downloaded MP4 from `~/Downloads`.
If protected URL download still fails but the page is complete and has a visible
top-right `下载` button, click the page button and then copy the newest MP4 from
`~/Downloads`. Quote the file path or use null-delimited `find -print0` patterns
because Xiaoyunque may save names such as `final_video (5).mp4`. See
`references/continue-confirm-download-runbook.md` for the full fallback
sequence.

## Completion Check

Before final response, report only verified facts:

- prompt/reference files saved;
- mode/model/duration/ratio seen on page;
- attachment filenames verified;
- prompt verified to contain no local image paths;
- credit charge or blocker observed;
- local MP4 path, `ffprobe` dimensions/duration, and copy targets.
