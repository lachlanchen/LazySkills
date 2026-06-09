# Continue Confirmation And Protected Download Runbook

Use this reference when a Xiaoyunque Agent or long-video thread pauses after
storyboard/material preparation, or when a finished video is visible but direct
media URL download fails.

## Continue A Paused Agent Thread

Agent workflows can pause with a message like:

```text
如符合预期我将继续生成视频。
```

Continue the existing thread instead of opening a new composer:

1. Inspect the tail of `document.body.innerText` and confirm it is asking for
   continuation.
2. Type a short reply such as `继续生成视频。` into the visible chat input.
3. Use real browser typing through `type-prompt`; raw DOM insertion can leave
   the send button disabled.
4. Click the visible send button and verify the thread advances to a generation
   step such as `generate_shot_video`.

Example:

Create an ignored temporary file such as `outputs/xyq-run/continue.md` with
exactly:

```text
继续生成视频。
```

Then type and send it:

```bash
scripts/xyq_cdp_browser.py type-prompt PAGE_ID outputs/xyq-run/continue.md --wait 0.3
scripts/xyq_cdp_browser.py eval PAGE_ID '(() => {
  const btn = [...document.querySelectorAll("button")]
    .find(b => String(b.className).includes("sendMessageTool"));
  const r = btn && btn.getBoundingClientRect();
  return {
    disabled: btn ? (btn.disabled || String(btn.className).includes("disabled")) : null,
    rect: r ? {x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height)} : null
  };
})()'
scripts/xyq_cdp_browser.py click PAGE_ID SEND_X SEND_Y
```

After sending, verify state:

```bash
scripts/xyq_cdp_browser.py eval PAGE_ID '(() => ({
  url: location.href,
  hasError: /错误|失败|积分不足|内部错误|not enough|credits/i.test(document.body.innerText),
  tail: document.body.innerText.slice(-1500),
  videos: [...document.querySelectorAll("video")].map(v => ({
    src: v.currentSrc || v.src,
    duration: v.duration,
    readyState: v.readyState
  }))
}))()'
```

## Watch Completion

Use the browser watcher first:

```bash
scripts/xyq_chrome/watch_thread_dom_download.py \
  --page-id PAGE_ID \
  --thread-url "THREAD_URL" \
  --output-dir outputs/xyq-run \
  --filename result.mp4 \
  --copy-to Videos \
  --interval 30 --max-polls 240 --reload-every 20
```

If it was launched without a TTY and must be stopped, find and kill the process:

```bash
pgrep -af 'watch_thread_dom_download.py.*THREAD_ID'
kill PID
```

## Protected URL Failure

Finished videos often expose signed `everphoto` or `365yg` URLs. External
`curl`, `urllib`, or watcher direct download may return HTTP errors even though
the logged-in browser can play the video.

When this happens:

1. Confirm a visible `<video>` exists.
2. Inspect buttons on the completed page.
3. Prefer the page's top-right `下载` button over repeated direct URL retries.
4. Watch `~/Downloads` for the newest MP4.
5. Copy the MP4 to the requested output folder and verify with `ffprobe`.

Inspection helper:

```bash
scripts/xyq_cdp_browser.py eval PAGE_ID '(() => {
  const visible = el => {
    const r = el.getBoundingClientRect();
    const s = getComputedStyle(el);
    return r.width > 2 && r.height > 2 && s.display !== "none" && s.visibility !== "hidden";
  };
  const rect = el => {
    const r = el.getBoundingClientRect();
    return {x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height)};
  };
  return {
    videos: [...document.querySelectorAll("video")].map(v => ({
      src: v.currentSrc || v.src,
      duration: v.duration,
      readyState: v.readyState,
      rect: rect(v)
    })),
    buttons: [...document.querySelectorAll("button,[role=button],a")]
      .filter(visible)
      .map((b, i) => ({
        i,
        text: (b.innerText || "").trim(),
        aria: b.getAttribute("aria-label"),
        cls: String(b.className).slice(0, 120),
        rect: rect(b),
        disabled: b.disabled || String(b.className).includes("disabled")
      }))
      .filter(b => /下载|download|导出|保存|去剪映|字幕擦除|提升画质/.test(`${b.text} ${b.aria || ""} ${b.cls}`))
  };
})()'
```

Click the visible download button:

```bash
scripts/xyq_cdp_browser.py click PAGE_ID DOWNLOAD_X DOWNLOAD_Y
find ~/Downloads -maxdepth 1 -type f -name '*.mp4' -printf '%T@ %s %p\n' \
  | sort -nr | head
```

Validate and copy:

```bash
ffprobe -v error \
  -show_entries format=duration,size \
  -show_entries stream=width,height,codec_name \
  -of default=noprint_wrappers=1 \
  ~/Downloads/FILE.mp4

cp -v ~/Downloads/FILE.mp4 Videos/readable_name.mp4
```

## Completion Report

Report verified facts only:

- completed thread URL;
- whether a continuation reply was sent;
- queue/render status if a job is still pending;
- downloaded source path and copied path;
- `ffprobe` duration, dimensions, codecs, and size;
- whether protected URL fallback or page download was used.
