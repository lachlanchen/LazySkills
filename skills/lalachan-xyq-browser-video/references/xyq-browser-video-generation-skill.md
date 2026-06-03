# Xiaoyunque Browser Video Generation Skill

This is the reusable local workflow for LALACHAN video generation through the Xiaoyunque web UI. It is intentionally browser-first: do not use the Xiaoyunque API unless the user explicitly requests it.

## Default Setup

Work in:

```bash
cd /home/lachlan/ProjectsLFS/LALACHAN
```

Use the controlled Chrome profile:

```text
CDP: http://127.0.0.1:9222
Profile: /home/lachlan/.cache/xyq-chrome
Launch: scripts/xyq_chrome/launch_chrome.sh
Page helper: scripts/xyq_cdp_browser.py
Watcher: scripts/xyq_chrome/watch_thread_dom_download.py
```

Start or inspect Chrome:

```bash
scripts/xyq_chrome/launch_chrome.sh "https://xyq.jianying.com/home?tab_name=integrated-agent"
scripts/xyq_cdp_browser.py list-pages
scripts/xyq_cdp_browser.py bring-to-front PAGE_ID
scripts/xyq_cdp_browser.py visible PAGE_ID
```

## Standard Short Video Contract

For ordinary LALACHAN short videos:

- Mode: `沉浸式短片`.
- Model: `Seedance 2.0 Fast`, normal/non-VIP unless explicitly requested.
- Duration: `15s`.
- Language: mainly Chinese, with short English/Japanese phrases only if useful.
- Prompt must include: `不要字幕，不要生成任何字幕、说明文字、下三分之一文字或画面文字。`

Default images:

```text
display.png
patchwork-leather-notebook-luxury-clean-v2.png
R1.jpg.jpeg
R3.jpg.jpeg
Trio.png
```

Use `Trio.png` as the role identity reference:

- 啦啦侠 / Lala Xia: giant panda.
- 阿芽酱 / Aya Chan: red panda.
- 飒飒君 / Sasa Kun: boy.

## Submit Flow

1. Save the story prompt in `references/prompts/YYYY-MM-DD-topic-15s.md`.
2. Save the exact Xiaoyunque submit prompt in `references/prompts/YYYY-MM-DD-topic-submit-15s.md`.
3. Open or reuse a Xiaoyunque `integrated-agent` tab.
4. Select `沉浸式短片`.
5. Select `Seedance 2.0 Fast`, not VIP, unless the user asks for VIP.
6. Set duration to `15秒`; current UI may use a slider.
7. Upload and verify the five images:

```bash
scripts/xyq_cdp_browser.py upload-images-verify PAGE_ID \
  display.png \
  patchwork-leather-notebook-luxury-clean-v2.png \
  R1.jpg.jpeg \
  R3.jpg.jpeg \
  Trio.png \
  --screenshot outputs/xyq-run/after-upload.png
```

8. Fill prompt with user-like typing:

```bash
scripts/xyq_cdp_browser.py type-prompt PAGE_ID references/prompts/YYYY-MM-DD-topic-submit-15s.md
```

9. Verify page state before submit: mode, model, duration, prompt, five filenames.
10. Submit only if requested. Record thread URL, page id, screenshot, and charged credits.

## Watch Flow

Use browser/CDP watch, not API:

```bash
tmux new-session -d -s xyq_watch "cd /home/lachlan/ProjectsLFS/LALACHAN && \
scripts/xyq_chrome/watch_thread_dom_download.py \
  --page-id PAGE_ID \
  --thread-url 'THREAD_URL' \
  --output-dir outputs/xyq-run \
  --filename result_15s.mp4 \
  --copy-to Videos \
  --copy-to '/home/lachlan/Nutstore Files/AutoPublish/AutoPublish' \
  --interval 30 --max-polls 240 --reload-every 300 \
  2>&1 | tee -a outputs/xyq-run/watch.log"
```

Check progress:

```bash
tail -80 outputs/xyq-run/watch.log
```

The watcher can see `排队等待中`, `优先处理中`, `生成中`, and `下载`. Direct media URLs can be protected and may return `403`; this is normal.

## Manual Download Fallback

If Xiaoyunque exposes the result but direct download fails, use browser/manual download, then copy from `~/Downloads`:

```bash
find ~/Downloads -maxdepth 1 -type f -name '*.mp4' -printf '%T@ %s %p\n' | sort -nr | head
cp -v ~/Downloads/FILE.mp4 "/home/lachlan/Nutstore Files/AutoPublish/AutoPublish/"
```

For two newest downloads:

```bash
DEST="/home/lachlan/Nutstore Files/AutoPublish/AutoPublish"
find ~/Downloads -maxdepth 1 -type f -name '*.mp4' -printf '%T@ %p\n' \
  | sort -nr | head -2 | cut -d' ' -f2- \
  | while IFS= read -r f; do cp -v "$f" "$DEST/"; done
```

## Evidence To Save

Save run-specific notes in `references/`, including:

- prompt files;
- screenshots under `outputs/xyq-.../`;
- page id and thread URL;
- submit time;
- model/mode/duration;
- attached filenames;
- watch log path;
- final copied output paths.
