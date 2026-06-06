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
references/xyq-browser-automation-workflow.md
references/smooth-video-generation-runbook.md
```

## LALACHAN Defaults

Default reference images in the LALACHAN project:

```text
display.png
patchwork-leather-notebook-luxury-clean-v2.png
R1.jpg.jpeg
R3.jpg.jpeg
Trio.png
```

Characters:

- `啦啦侠 / Lala Xia`: giant panda from `Trio.png`.
- `阿芽酱 / Aya Chan`: red panda from `Trio.png`.
- `飒飒君 / Sasa Kun`: boy from `Trio.png`.
- `display.png`: LightMind AI glasses.
- `patchwork-leather-notebook-luxury-clean-v2.png`: handmade patchwork notebook/tool prop.

Default short-video setup:

```text
Mode: 沉浸式短片
Model: Seedance 2.0 Fast normal/non-VIP, or Seedance 2.0 normal/non-VIP for lower credit budgets
Duration: 15s
Ratio: 4:3 unless the user requests otherwise
Prompt language: mainly Chinese
Always include: 不要字幕，不要生成任何字幕、说明文字、下三分之一文字或画面文字。
```

## Credit-Budget Rule

- If the user mentions a low budget, "last night model", "no VIP", or about 200 points, use `沉浸式短片`.
- Inspect the model dropdown and avoid any option containing `VIP`.
- If `Seedance 2.0` normal/non-VIP is available and the toolbar shows about `8/S`, prefer it for 15s because it costs about 120 points.
- Do not continue an `智能长视频` / Agent render if the final video cost exceeds the user's budget; switch to short-video workflow or report the blocker.
- For `4:3`, verify the opened ratio menu checkmark or screenshot because the compact toolbar may still show only `比例`.

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
  display.png patchwork-leather-notebook-luxury-clean-v2.png \
  R1.jpg.jpeg R3.jpg.jpeg Trio.png \
  --timeout 180 \
  --screenshot outputs/xyq-run/after-upload.png
```

5. Fill the saved prompt:

```bash
scripts/xyq_cdp_browser.py --cdp-url http://127.0.0.1:9222 type-prompt PAGE_ID references/prompts/example.md --wait 2
```

6. If the submit button stays disabled, inspect upload item classes. Wait until every uploaded file item is `success`; a single `uploading` reference blocks submission.

7. Submit only when the user asked for generation and the pre-submit contract is satisfied.

## Watch, Download, Copy

Monitor the submitted thread through the browser page:

```bash
scripts/xyq_chrome/watch_thread_dom_download.py \
  --cdp-url http://127.0.0.1:9222 \
  --page-id PAGE_ID \
  --thread-url "THREAD_URL" \
  --output-dir outputs/xyq-run \
  --filename result_15s.mp4 \
  --copy-to Videos \
  --copy-to "/home/lachlan/Nutstore Files/AutoPublish/AutoPublish"
```

Protected `everphoto` URLs may fail from unauthenticated direct HTTP. First test browser-context fetch with `--await-promise`; if it returns `200 video/mp4`, pull the active `video.currentSrc` from the page and download with browser-like `Referer` and `User-Agent` headers.
The bundled watcher can now use this same browser-context path by triggering an
in-page blob download and copying the downloaded MP4 from `~/Downloads`.

## Completion Check

Before final response, report only verified facts:

- prompt/reference files saved;
- mode/model/duration/ratio seen on page;
- attachment filenames verified;
- credit charge or blocker observed;
- local MP4 path, `ffprobe` dimensions/duration, and copy targets.
