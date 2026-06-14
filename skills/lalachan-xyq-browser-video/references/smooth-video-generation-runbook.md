# Smooth Xiaoyunque Browser Video Generation

This runbook captures the reliable browser-first method for Xiaoyunque video
generation. It is designed for Codex, AgInTi, Claude, Gemini, Copilot, and other
agents that can run shell commands and control a logged-in Chrome/CDP browser.

## Pre-Submit Contract

Before clicking generate, prove these facts from the visible page or DOM:

- correct mode, usually `沉浸式短片` for short videos;
- non-VIP model unless the user explicitly asks for VIP;
- requested duration, usually `15秒`;
- requested ratio, currently default `4:3` for LALACHAN;
- prompt contains the no-subtitle/no-screen-text requirement;
- prompt contains no local filesystem paths or filenames; references should be
  described by uploaded image order such as `图1` through `图7`;
- all reference images or videos are attached and no upload item is still
  `uploading`;
- submit button exists and is enabled.

## Controlled Browser

Use the logged-in CDP browser instead of an API call:

```bash
curl -fsS http://127.0.0.1:9222/json/list
scripts/xyq_cdp_browser.py list-pages
```

If Chrome is visible but the endpoint refuses connections, it is not the
controlled browser. Relaunch the persistent profile before uploading or
submitting.

If the Xiaoyunque page is blank or infinite-loading, recover the same tab. This
is equivalent to `Ctrl+L`, `Enter`:

```bash
scripts/xyq_cdp_browser.py navigate PAGE_ID \
  "https://xyq.jianying.com/home?tab_name=integrated-agent"
sleep 8
scripts/xyq_cdp_browser.py visible PAGE_ID
```

Do not open a new tab for this recovery.

If the old thread is stale or already completed, use the page `创作` /
new-session control in the same controlled tab and record the new thread URL.
Avoid accumulating extra tabs.

## Submit Pattern

```bash
scripts/xyq_cdp_browser.py upload-images-verify PAGE_ID \
  words-card.jpg \
  LazyingArtRobot.png display.png patchwork-leather-notebook-luxury-clean-v2.png \
  R1.jpg.jpeg R3.jpg.jpeg Trio.png \
  --timeout 180 \
  --screenshot outputs/run/after-upload.png
```

```bash
scripts/xyq_cdp_browser.py type-prompt PAGE_ID references/prompts/submit.md
```

Before filling the page, reject prompt files that leak local image paths:

```bash
rg -n '/home|ProjectsLFS|artifacts|\.png|\.jpg|\.jpeg' references/prompts/submit.md || true
```

Re-query the create button rectangle immediately before submitting. Xiaoyunque
can move the arrow after attachments expand the composer, and stale coordinates
may do nothing.

## Watch And Download

```bash
scripts/xyq_chrome/watch_thread_dom_download.py \
  --page-id PAGE_ID \
  --thread-url THREAD_URL \
  --output-dir outputs/run \
  --filename result.mp4 \
  --copy-to Videos
```

Protected result URLs may fail through direct HTTP. The watcher should then test
the active `video.currentSrc` inside the logged-in page. If browser-context
`fetch(..., {credentials: 'include'})` returns `200 video/mp4`, trigger an
in-page blob download, wait for the file in `~/Downloads`, copy it to the output
path, and verify with `ffprobe`.

## Verification

```bash
ffprobe -v error \
  -show_entries format=duration,size \
  -show_entries stream=width,height,codec_name \
  -of json Videos/result.mp4
```

```bash
ffmpeg -y -loglevel error -i Videos/result.mp4 \
  -vf "select='eq(n,20)+eq(n,180)+eq(n,330)',scale=480:-1,tile=3x1" \
  -frames:v 1 outputs/run/contact_sheet.jpg
```

Report verified paths, dimensions, duration, model, mode, ratio, and whether the
job used browser UI rather than API.
