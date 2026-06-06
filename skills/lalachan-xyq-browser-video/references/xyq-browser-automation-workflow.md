# Xiaoyunque Browser Automation Workflow

This records the browser-control work for 小云雀.

## What Happened In This Session

The already-open Chrome tab was visible and controllable through X11 screenshots and clicks. The target window title was:

```text
小云雀网页版 - Google Chrome
```

The target URL was:

```text
https://xyq.jianying.com/home?tab_name=integrated-agent&thread_id=e8217789-9938-4ebc-9e2f-f63a26a8db82&source=home_prompt&entrance_from=home
```

The external-link SVG provided by the user matched the visible `lucide-external-link` icon in the 小云雀 page. Clicking the visible icon opened a non-destructive video preview modal, confirming the page could be controlled at the UI level.

## Why The Existing Chrome Could Not Be CDP-Attached

The running Chrome process was launched as:

```text
/opt/google/chrome/chrome
```

It did not include:

```text
--remote-debugging-port=9222
```

Chrome DevTools Protocol and ChromeDriver-style attachment require the browser to be started with a remote-debugging port. A normal already-running Chrome tab cannot be attached later through CDP.

## Reusable CDP Launch

Use the controlled launch script:

```bash
scripts/xyq_chrome/launch_chrome.sh "https://xyq.jianying.com/home?tab_name=integrated-agent"
```

It launches Chrome with:

```bash
--remote-debugging-port=9222
--remote-allow-origins=http://127.0.0.1:9222
--user-data-dir=$HOME/.cache/xyq-chrome
```

The `--user-data-dir` preserves login state for future automated sessions.

## Reusable Driver Identity

For later Xiaoyunque work, reuse the same controlled driver instead of opening a normal Chrome tab:

```text
CDP endpoint: http://127.0.0.1:9222
Profile: /home/lachlan/.cache/xyq-chrome
Launch script: scripts/xyq_chrome/launch_chrome.sh
Attach helper: scripts/xyq_chrome/xyq_cdp.py
```

Check whether the driver is still alive:

```bash
curl -fsS http://127.0.0.1:9222/json/version
scripts/xyq_chrome/xyq_cdp.py --state
ps -eo pid,ppid,stat,etime,cmd | rg 'remote-debugging-port=9222|xyq-chrome'
```

If it is not alive, restart it:

```bash
scripts/xyq_chrome/launch_chrome.sh \
  "https://xyq.jianying.com/home?tab_name=integrated-agent"
```

Log in once in this profile. The login is stored under `/home/lachlan/.cache/xyq-chrome`, so later CDP runs can attach directly.

## Reusable CDP Tool

Use:

```bash
scripts/xyq_chrome/xyq_cdp.py
```

For quick control of an already-open Xiaoyunque tab by explicit page id, use:

```bash
scripts/xyq_cdp_browser.py
```

This helper was added on `2026-05-09` for the bottom `+ -> 从资产库选择` workflow. It can list tabs, inspect visible controls, click coordinates, take screenshots, run JavaScript probes, and set the Tiptap prompt safely.

Print page state:

```bash
scripts/xyq_chrome/xyq_cdp.py --state
```

Fill the visible prompt composer without submitting:

```bash
scripts/xyq_chrome/xyq_cdp.py --fill-prompt-file references/prompts/example.md
```

Click an indexed `lucide-external-link` icon:

```bash
scripts/xyq_chrome/xyq_cdp.py --click-external-link 0
```

Run a custom JavaScript probe:

```bash
scripts/xyq_chrome/xyq_cdp.py --eval "location.href"
```

List current CDP pages with the new helper:

```bash
scripts/xyq_cdp_browser.py list-pages
```

Bring a controlled background CDP page to the visible Chrome foreground:

```bash
scripts/xyq_cdp_browser.py bring-to-front PAGE_ID
```

Inspect the current composer controls:

```bash
scripts/xyq_cdp_browser.py visible PAGE_ID
```

Set a prompt without corrupting text:

```bash
scripts/xyq_cdp_browser.py set-prompt PAGE_ID references/prompts/example.md
```

For Xiaoyunque's React/Tiptap composer, prefer user-like CDP typing when the
submit button needs to become enabled:

```bash
scripts/xyq_cdp_browser.py type-prompt PAGE_ID references/prompts/example.md
```

Select the short-video mode without accidentally clicking a history item:

```bash
scripts/xyq_cdp_browser.py select-mode PAGE_ID "沉浸式短片"
```

Upload local image reference files into the visible composer:

```bash
scripts/xyq_cdp_browser.py upload-images-verify PAGE_ID \
  display.png patchwork-leather-notebook-luxury-clean-v2.png R1.jpg.jpeg R3.jpg.jpeg Trio.png \
  --screenshot outputs/xyq-run/after_upload.png
```

The helper now chooses the image/material file input by default and avoids the
hidden `.json` preset importer. If the page shows `导入预设失败，请检查文件格式`,
the wrong input was used; retry with the helper above or explicitly select the
non-JSON upload input. `scripts/xyq_cdp_browser.py wait` takes seconds, or
`PAGE_ID seconds`; `PAGE_ID` alone is only a short pause.

Select Xiaoyunque modes from the home composer:

```bash
scripts/xyq_chrome/xyq_cdp.py --url "https://xyq.jianying.com/home?tab_name=home" --select-mode agent
scripts/xyq_chrome/xyq_cdp.py --url "https://xyq.jianying.com/home?tab_name=home" --select-mode duanpian
scripts/xyq_chrome/xyq_cdp.py --url "https://xyq.jianying.com/home?tab_name=home" --select-mode long2
```

Use the dedicated short-drama Agent workspace directly:

```bash
scripts/xyq_chrome/xyq_cdp.py \
  --url "https://xyq.jianying.com/novel/list?enter_from=small_tool" \
  --state
```

Poll a submitted Xiaoyunque browser thread and download the first finished MP4:

```bash
scripts/xyq_chrome/poll_result_download.py \
  --page-id-file outputs/xyq-episode07-supernova-web-normal-fast/page_id.txt \
  --thread-url "https://xyq.jianying.com/home?tab_name=integrated-agent&thread_id=THREAD_ID&source=home_prompt&entrance_from=home" \
  --output-dir outputs/xyq-episode07-supernova-web-normal-fast \
  --filename episode07_supernova_sneeze_15s.mp4 \
  --copy-to-videos Videos
```

This tool only watches an already-submitted web task. It does not call the
Xiaoyunque API and does not start a new generation. If the CDP target is
closed or disappears, it reopens the same `thread_id` URL and continues
polling.

Newer browser watcher for current Xiaoyunque thread DOM/status:

```bash
scripts/xyq_chrome/watch_thread_dom_download.py \
  --page-id PAGE_ID \
  --thread-url "https://xyq.jianying.com/home?tab_name=integrated-agent&thread_id=THREAD_ID&agent_name=pippit_video_part_agent" \
  --output-dir outputs/xyq-run \
  --filename result_15s.mp4 \
  --copy-to Videos \
  --copy-to "/home/lachlan/Nutstore Files/AutoPublish/AutoPublish"
```

This watcher recognizes normal queue, VIP priority queue, generation, and
download states. Some Xiaoyunque media URLs are protected and return `403` when
downloaded outside the page. If that happens, download manually in the browser
or use the visible page download button, then copy the newest MP4 from
`~/Downloads` to Nutstore.

Concise reusable runbook:

```text
references/xyq-browser-video-generation-skill.md
```

Successful 2026-06-02 Hokkaido run:

```text
references/xyq-hokkaido-dolphin-shark-web-run-2026-06-02.md
```

Run the non-destructive mode smoke test:

```bash
scripts/xyq_chrome/test_modes.py --output references/xyq-mode-test-results.md
```

Prepare the dedicated short-drama Agent from the saved ChatGPT draft:

```bash
scripts/xyq_chrome/prepare_duanju_from_chatgpt.py
```

This uploads `Lala-Aya-Sasa-draft/duanju-agent-chatgpt-sushi.txt` to the `/novel/list` workspace, reuses `Trio.png` as the default character reference asset, waits for `剧本解析`, and does not submit generation.

Send a new synopsis into the existing ChatGPT script thread and save the answer:

```bash
scripts/xyq_chrome/chatgpt_thread_prompt.py \
  --prompt-file Lala-Aya-Sasa-draft/2026-05-09-today-script-synopsis.md \
  --output Lala-Aya-Sasa-draft/2026-05-09-hong-kong-rainy-tea-restaurant-chatgpt.md
```

This attaches to:

```text
https://chatgpt.com/c/69fc0bcd-4f2c-83ea-9117-46fc128a2496
```

It fills the visible ChatGPT composer, sends the prompt, waits for the new assistant message to stop changing, then writes a Markdown copy containing both the prompt and the response.

## Attach Test Result

The controlled Chrome launch was tested on `2026-05-08` with the thread URL above. After startup, Chrome listened on:

```text
127.0.0.1:9222
```

The CDP state probe succeeded:

```bash
scripts/xyq_chrome/xyq_cdp.py --state
```

Because the controlled profile was new, 小云雀 redirected to:

```text
https://xyq.jianying.com/login?redirect_url=%2Fhome%3Ftab_name%3Dintegrated-agent
```

Log in once in the controlled profile before using prompt-fill automation on the real workspace page.

After login, the same CDP state probe attached successfully to:

```text
https://xyq.jianying.com/home?tab_name=integrated-agent&thread_id=c883f4a0-8ffb-43ff-bf1a-2a8c1fffee82
```

It found one visible prompt composer and the page buttons, confirming the controlled driver profile is ready for prompt-fill automation.

## X11 Fallback Used For The Existing Tab

Because the existing Chrome tab lacked CDP, X11 was used for non-destructive tests:

- Enumerated windows with `python-xlib`.
- Focused the 小云雀 Chrome window by X11 window id.
- Captured screenshots with `window.get_image(...)` and Pillow.
- Sent harmless keys/clicks with `Xlib.ext.xtest`.
- Confirmed the external-link icon opened a preview modal.

This is useful for inspection, but CDP is the preferred method for robust prompt filling and state checks.

## Recommended Future Workflow

1. Launch 小云雀 with `scripts/xyq_chrome/launch_chrome.sh`.
2. Confirm `http://127.0.0.1:9222/json/list` responds. If it does not, the visible Chrome is not the controlled driver browser.
3. Log in once in that controlled profile if needed.
4. If the Xiaoyunque page is blank or `visible PAGE_ID` returns no usable text, recover the same tab by re-entering the address (`Ctrl+L`, `Enter`) or by CDP `navigate` to the same URL. Do not open a new tab for this.
5. Use `scripts/xyq_chrome/xyq_cdp.py --state` to confirm the page and editable fields.
6. For standard LALACHAN short videos, verify the ratio menu is set to `4:3`; the compact toolbar may only show `比例`.
7. Use `--fill-prompt-file` to fill generated prompts.
8. Submit manually or add an explicit submit helper only after verifying the send button selector on the page.

For reference-video generation through the API and browser driver together, use:

```bash
scripts/xyq_chrome/reference_video_until_credit.py \
  --video path/to/reference.mp4 \
  --thread-id THREAD_ID \
  --json-log outputs/xyq-reference-video-run.json
```

This uploads the reference file, fills the visible browser composer for traceability, submits the run through the Xiaoyunque skill API, auto-confirms once when asked, and stops on an insufficient-credit block or terminal run state.

For the current preferred web UI reference-video path, see:

```text
references/xyq-asset-library-reference-workflow.md
```

Important distinction:

- Bottom `+ -> 从资产库选择` attaches actual old generated videos as references.
- `@引用素材` is not the preferred path for old reference-video selection.
- Do not write UI steps into the prompt; attach the assets first, then keep the prompt focused on the story and `不要字幕`.

- 2026-05-10: 通过 `uploadMenuItem-GDs2iL` 文本选择“从资产库选择”可复现。

## 2026-05-12 Fast Path: Episode 03 Short Film

This is the exact browser-driver workflow used for the `星钥孵出的恐龙`
15s Xiaoyunque preparation. It used the logged-in Chrome tab only. Do not use
the Xiaoyunque API for this path unless the user explicitly asks for it.

Saved prompt:

```text
references/prompts/2026-05-12-episode03-xingyao-dinosaur-duanpian-15s.md
```

Default five local photos for this run:

```text
/home/lachlan/ProjectsLFS/LALACHAN/display.png
/home/lachlan/ProjectsLFS/LALACHAN/patchwork-leather-notebook-luxury-clean-v2.png
/home/lachlan/ProjectsLFS/LALACHAN/R1.jpg.jpeg
/home/lachlan/ProjectsLFS/LALACHAN/R3.jpg.jpeg
/home/lachlan/ProjectsLFS/LALACHAN/Trio.png
```

List tabs and choose the existing Xiaoyunque page:

```bash
scripts/xyq_cdp_browser.py list-pages
PAGE_ID=A9FBAB250CD9E5D028CD0171B5168B03
```

Select `沉浸式短片` from the home composer:

```bash
scripts/xyq_chrome/xyq_cdp.py \
  --url "https://xyq.jianying.com/home?tab_name=home" \
  --select-mode duanpian
```

Set the model to non-VIP `Seedance 2.0 Fast`:

```bash
# Inspect model dropdown contents after opening it.
scripts/xyq_cdp_browser.py visible "$PAGE_ID"

# Today the non-VIP row was visible around this point after the dropdown opened.
scripts/xyq_cdp_browser.py click "$PAGE_ID" 815 683
```

Confirm the page says non-VIP Fast, not `Fast VIP`:

```bash
scripts/xyq_cdp_browser.py eval "$PAGE_ID" \
"(() => ({
  model:(document.querySelector('.triggerButton-JhN19_')?.innerText||'').trim(),
  credit:(document.querySelector('.creditTip-csIAa4')?.innerText||'').trim()
}))()"
```

Expected result:

```json
{
  "model": "2.0 Fast",
  "credit": "沉浸式短片 Seedance 2.0 Fast 按 1 秒 5 积分扣除"
}
```

Set duration to `15秒`. If the slider is open, set it by clicking near the far
right of the slider. Confirm with:

```bash
scripts/xyq_cdp_browser.py eval "$PAGE_ID" \
"(() => [...document.querySelectorAll('button')]
  .find(b => (b.innerText || '').includes('秒'))?.innerText || '')()"
```

Fill the prompt:

```bash
scripts/xyq_cdp_browser.py set-prompt "$PAGE_ID" \
  references/prompts/2026-05-12-episode03-xingyao-dinosaur-duanpian-15s.md
```

Attach old generated video through the bottom `+` menu, not through `@`:

```bash
# The plus button position changes when the prompt grows; inspect first.
scripts/xyq_cdp_browser.py visible "$PAGE_ID"

# Open bottom + menu, then choose 从资产库选择.
scripts/xyq_cdp_browser.py click "$PAGE_ID" 484 666
scripts/xyq_cdp_browser.py click "$PAGE_ID" 575 571
```

In the asset modal, select an old trio/video reference such as
`comet_shortfilm.mp4`, then click `应用`. Use screenshots when the visible list
is ambiguous:

```bash
scripts/xyq_cdp_browser.py screenshot "$PAGE_ID" /tmp/xyq_asset_picker.png
```

Upload the five local photos directly through the hidden composer upload input.
Prefer `upload-images-verify` for new runs because it uploads, polls visible
thumbnail evidence, matches filenames, and writes a screenshot in one step:

```bash
scripts/xyq_cdp_browser.py upload-images-verify "$PAGE_ID" \
  display.png \
  patchwork-leather-notebook-luxury-clean-v2.png \
  Trio.png \
  R1.jpg.jpeg \
  R3.jpg.jpeg \
  --screenshot outputs/xyq-upload-training/upload-verification.png
```

If working step-by-step, `set-file-input` is still valid, but it only proves the
browser accepted the files. Always follow it with DOM verification:

```bash
scripts/xyq_cdp_browser.py set-file-input "$PAGE_ID" \
  display.png \
  patchwork-leather-notebook-luxury-clean-v2.png \
  Trio.png \
  R1.jpg.jpeg \
  R3.jpg.jpeg \
  --index 0

scripts/xyq_cdp_browser.py verify-attachments "$PAGE_ID"
```

For a correct five-image upload, the DOM should show `assetCount` as `5/10` and
filename evidence for:

```text
display.png
patchwork-leather-notebook-luxury-clean-v2.png
Trio.png
R1.jpg.jpeg
R3.jpg.jpeg
```

If DOM verification succeeds but the user cannot see the images, you probably
uploaded to a background CDP page or a different Xiaoyunque workflow. Run
`list-pages`, compare the exact URL (`home`, `integrated-agent`, `montage`,
etc.), then run `bring-to-front PAGE_ID` and take a fresh screenshot. Reports
must name both the page id and workflow; do not say the user-visible page has
the images unless the foreground screenshot proves it.

If one image is missing, upload only that file rather than re-uploading
everything. Example from 2026-05-19:

```bash
scripts/xyq_cdp_browser.py set-file-input "$PAGE_ID" \
  patchwork-leather-notebook-luxury-clean-v2.png

scripts/xyq_cdp_browser.py eval "$PAGE_ID" \
"(() => {
  const v = el => {
    const r=el.getBoundingClientRect(), s=getComputedStyle(el);
    return r.width>2 && r.height>2 && s.display!=='none' && s.visibility!=='hidden';
  };
  const t = el => (el && (el.innerText || el.textContent || '')).trim();
  const assetCount = ([...document.querySelectorAll('[class*=assetCount]')].filter(v)[0]?.innerText || '').trim();
  const patchworkFound = [...document.querySelectorAll('[class*=materialCard]')]
    .filter(v).some(el => t(el).includes('patchwork-leather-notebook-luxury-clean-v2.png'));
  return {assetCount, patchworkFound};
})()"
```

Wait until every local image shows as an attached material, then verify attached
assets, model, duration, and prompt length:

```bash
scripts/xyq_cdp_browser.py eval "$PAGE_ID" \
"(() => {
  const items=[...document.querySelectorAll('[class*=fileItem]')]
    .map((el,i)=>({i,text:(el.innerText||'').trim().replace(/\\n/g,' | '),
      cls:String(el.className)}));
  return {
    model:(document.querySelector('.triggerButton-JhN19_')?.innerText||'').trim(),
    credit:(document.querySelector('.creditTip-csIAa4')?.innerText||'').trim(),
    duration:[...document.querySelectorAll('button')]
      .find(b=>(b.innerText||'').includes('秒'))?.innerText||'',
    items,
    promptLen:(document.querySelector('.editor-HT1dqv')?.innerText||'').length
  };
})()"
```

Expected attachment list for this run:

```text
display.png
patchwork-leather-notebook-luxury-clean-v2.png
Trio.png
R1.jpg.jpeg
R3.jpg.jpeg
comet_shortfilm.mp4 0:15
```

If an accidental extra asset-library image appears before the five photos,
remove it using the small remove button on its thumbnail. Today the first
thumbnail remove button was around:

```bash
scripts/xyq_cdp_browser.py click "$PAGE_ID" 514 339
```

Submit only after the user confirms, or if the user explicitly asks Codex to
start generation:

```bash
scripts/xyq_cdp_browser.py click "$PAGE_ID" 1186 753
```

Notes from this run:

- The top banner may advertise `Seedance 2.0 Fast VIP`; ignore the banner.
- The actual model is the toolbar model selector. It must read `2.0 Fast`.
- With a reference video attached, the credit line changed to `带参考视频` and
  `1 秒 10 积分`.
- The UI displays attached files with `@` marks even when they were attached
  correctly through `+` or the file input. This is fine; the mistake is using
  the separate toolbar `@引用素材` control for old generated video selection.
- Always include `不要字幕，不要生成任何字幕、说明文字、下三分之一文字或画面文字。`
- The bottom `+` button is `triggerButton-bisRxS`; after clicking it, the
  upload menu items are visible in the DOM.
- Text-clicking `从资产库选择` is more reliable than using the toolbar `@` button.
