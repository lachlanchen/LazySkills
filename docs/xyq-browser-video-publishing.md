# Xiaoyunque Browser Video Publishing Workflow

This document records the browser-first method used to generate, download, and publish a LALACHAN Xiaoyunque video without using the Xiaoyunque API.

## Successful Path

1. Use the logged-in Chrome/CDP page instead of API submission.
2. Select `沉浸式短片`.
3. Select a non-VIP model. For the low-credit run, `Seedance 2.0` showed `8/S`, so 15s cost about 120 points.
4. Set duration to `15秒`.
5. Set ratio to `4:3` and verify it by reopening the ratio dropdown because the toolbar may still show only `比例`.
6. Upload all five reference images and wait until every file item is `success`.
7. Fill a compact prompt that includes no-subtitle/no-text requirements.
8. Submit from the actual enabled submit button coordinates, not stale toolbar coordinates.
9. Poll the generation thread until a video appears.
10. Download the protected media URL with browser-like headers if the watcher cannot fetch it directly.
11. Verify with `ffprobe`, copy to `Videos/`, and copy to Nutstore AutoPublish.

## Problems Met

- The long-video Agent path created a ~93s plan and requested 1023 points, exceeding the available 869 points.
- The browser CDP port changed; the active controlled page was on `http://127.0.0.1:9344`.
- The ratio toolbar label did not display `4:3`; the dropdown checkmark was the reliable evidence.
- One reference image stayed in `uploading`, which kept the submit button disabled.
- The submit arrow moved after attachments expanded the composer; clicking old coordinates did nothing.
- Direct watcher downloads from protected `everphoto` URLs returned HTTP errors.
- Nutstore AutoPublish renamed the copied file to a `_COMPLETED.mp4` filename.

## Tools Used

- `xyq_cdp_browser.py`: list pages, inspect visible controls, upload images, fill prompts, click buttons, and evaluate DOM state.
- `watch_thread_dom_download.py`: poll submitted Xiaoyunque threads and detect video resources.
- `curl`: download the browser-exposed protected `video.currentSrc` with `Referer` and `User-Agent` headers.
- `ffprobe`: verify dimensions, streams, and duration.
- `ffmpeg`: extract a mid-frame for visual sanity checks.
- `git` and `gh`: commit and publish reusable docs/skills.

## Core Commands

```bash
skills/lalachan-xyq-browser-video/scripts/xyq_cdp_browser.py \
  --cdp-url http://127.0.0.1:9344 list-pages
```

```bash
skills/lalachan-xyq-browser-video/scripts/xyq_cdp_browser.py \
  --cdp-url http://127.0.0.1:9344 upload-images-verify PAGE_ID \
  display.png patchwork-leather-notebook-luxury-clean-v2.png \
  R1.jpg.jpeg R3.jpg.jpeg Trio.png \
  --timeout 180 \
  --screenshot outputs/run/after-upload.png
```

```bash
skills/lalachan-xyq-browser-video/scripts/xyq_chrome/watch_thread_dom_download.py \
  --cdp-url http://127.0.0.1:9344 \
  --page-id PAGE_ID \
  --thread-url THREAD_URL \
  --output-dir outputs/run \
  --filename result.mp4 \
  --copy-to Videos \
  --copy-to "/home/lachlan/Nutstore Files/AutoPublish/AutoPublish"
```

Protected URL fallback:

```bash
url=$(skills/lalachan-xyq-browser-video/scripts/xyq_cdp_browser.py \
  --cdp-url http://127.0.0.1:9344 eval PAGE_ID \
  '(() => ({url: document.querySelector("video")?.currentSrc || document.querySelector("video")?.src || ""}))()' \
  | jq -r .url)

curl -fL --retry 3 --retry-delay 2 \
  -H 'Referer: https://xyq.jianying.com/' \
  -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36' \
  "$url" -o result.mp4
```

## Validation Checklist

- Page shows requested mode, model, duration, and point cost.
- Ratio dropdown confirms the desired ratio.
- All upload cards are `success`.
- Prompt contains `不要字幕` and no on-screen-text requirements.
- Output MP4 passes `ffprobe`.
- A frame extracted by `ffmpeg` is visually nonblank.
- Nutstore file appears or is renamed by AutoPublish.
