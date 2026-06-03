# Xiaoyunque Low-Credit Browser Video Workflow

Date: 2026-06-03

This note records the low-credit Xiaoyunque browser workflow used for the LALACHAN typhoon ping-pong shark video. It avoids the Xiaoyunque API and uses the logged-in Chrome/CDP web UI.

## Why This Path

The earlier `智能长视频` / Agent path generated a ~93s storyboard and then requested 1023 points for final rendering. The account had 869 points, so that path was blocked. For a budget around 200 points, use `沉浸式短片` instead.

Validated low-credit settings:

- Mode: `沉浸式短片`
- Model: `Seedance 2.0`, normal/non-VIP, not Fast
- Duration: `15秒`
- Ratio: `4:3`
- Cost indicator: `8/S`, about 120 points for 15s
- Subtitles/text: prompt explicitly says no subtitles and no on-screen text

## Prompt

Saved prompt:

```text
references/prompts/2026-06-03-typhoon-pingpong-shark-duanpian-15s-4x3-budget200.md
```

The prompt is intentionally compact because the short-video composer kept the submit button disabled until one upload finished and a tighter prompt was used. Keep the main story beats but avoid long meta-instructions in this mode.

## Browser Setup

Active controlled Chrome/CDP endpoint:

```bash
http://127.0.0.1:9344
```

Active Xiaoyunque page:

```text
4A2881C4526B7E299804F8117A02A9C5
```

Submitted thread:

```text
https://xyq.jianying.com/home?tab_name=integrated-agent&thread_id=8373accd-2c1a-4385-806c-4e6bfb49aa00&agent_name=pippit_video_part_agent
```

## Key Commands

List pages:

```bash
scripts/xyq_cdp_browser.py --cdp-url http://127.0.0.1:9344 list-pages
```

Upload and verify five references:

```bash
scripts/xyq_cdp_browser.py --cdp-url http://127.0.0.1:9344 upload-images-verify \
  4A2881C4526B7E299804F8117A02A9C5 \
  display.png patchwork-leather-notebook-luxury-clean-v2.png \
  R1.jpg.jpeg R3.jpg.jpeg Trio.png \
  --timeout 180 \
  --screenshot outputs/xyq-2026-06-03-typhoon/duanpian-upload-five.png
```

Fill the prompt:

```bash
scripts/xyq_cdp_browser.py --cdp-url http://127.0.0.1:9344 type-prompt \
  4A2881C4526B7E299804F8117A02A9C5 \
  references/prompts/2026-06-03-typhoon-pingpong-shark-duanpian-15s-4x3-budget200.md \
  --wait 2
```

Watch, download, and copy:

```bash
scripts/xyq_chrome/watch_thread_dom_download.py \
  --cdp-url http://127.0.0.1:9344 \
  --page-id 4A2881C4526B7E299804F8117A02A9C5 \
  --thread-url 'https://xyq.jianying.com/home?tab_name=integrated-agent&thread_id=8373accd-2c1a-4385-806c-4e6bfb49aa00&agent_name=pippit_video_part_agent' \
  --output-dir outputs/xyq-2026-06-03-typhoon \
  --filename typhoon_pingpong_shark_duanpian_4x3_15s.mp4 \
  --copy-to Videos \
  --copy-to '/home/lachlan/Nutstore Files/AutoPublish/AutoPublish' \
  --interval 10 \
  --max-polls 720 \
  --reload-every 600
```

If the watcher sees the video element but direct candidate downloads fail with protected `everphoto` HTTP errors, pull the active video URL from the logged-in page and download with browser-like headers:

```bash
out='outputs/xyq-2026-06-03-typhoon/typhoon_pingpong_shark_duanpian_4x3_15s.mp4'
url=$(scripts/xyq_cdp_browser.py --cdp-url http://127.0.0.1:9344 eval \
  4A2881C4526B7E299804F8117A02A9C5 \
  '(() => ({url: document.querySelector("video")?.currentSrc || document.querySelector("video")?.src || ""}))()' \
  | jq -r .url)
curl -fL --retry 3 --retry-delay 2 \
  -H 'Referer: https://xyq.jianying.com/' \
  -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36' \
  "$url" -o "$out"
```

## Validation Notes

- The ratio menu screenshot `outputs/xyq-2026-06-03-typhoon/ratio-menu-after-43.png` shows `4:3` checked.
- The ready screenshot `outputs/xyq-2026-06-03-typhoon/duanpian-ready-submit.png` shows the composer before submission.
- One attachment (`R3.jpg.jpeg`) remained in `uploading` state for a while; wait until all file items show `success` before submitting.
- Do not rely on the toolbar label alone for ratio because it may keep showing the generic word `比例`.

## Result

Generation was submitted at 2026-06-03 22:20:34. Initial status was `排队等待中`, with estimated wait around 30 minutes. The account charged 120 points, reducing the visible balance from 869 to 749.

Generated video:

```text
outputs/xyq-2026-06-03-typhoon/typhoon_pingpong_shark_duanpian_4x3_15s.mp4
Videos/typhoon_pingpong_shark_duanpian_4x3_15s.mp4
/home/lachlan/Nutstore Files/AutoPublish/AutoPublish/typhoon_pingpong_shark_duanpian_4x3_15s_2026_06_03_22_46_26_COMPLETED.mp4
```

`ffprobe` result:

```text
width=1112
height=836
duration=15.084s
```
