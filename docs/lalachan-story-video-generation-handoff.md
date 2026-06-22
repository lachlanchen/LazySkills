# LALACHAN Story and Video Generation Handoff

Use this note when a WeChat-monitored agent needs to create a daily LALACHAN story, generate the Xiaoyunque video, download it, and optionally publish through LazyEdit.

## WeChat Message Template

```text
请帮我完成今天的 LALACHAN 视频任务：
1. 先写一个自然、好懂、有趣的中文故事，角色是啦啦侠、阿芽酱、飒飒君、庄子机器人。
2. 保存故事到 $LALACHAN_ROOT/references/stories/。
3. 改成小云雀可用提示词，保存到 $LALACHAN_ROOT/references/prompts/。
4. 用浏览器 UI，不要用小云雀 API。上传参考图，选择沉浸式短片，默认用相对便宜且满足任务的 Seedance 模型；优先用 `Seedance 2.0 Mini 体验版` / `vipnew` 单秒约 4 积分，不可用时选相对便宜合适的 `Fast`、`Fast VIP` 或其它 Seedance 选项并继续。15s 默认，4:3 默认。
5. 提交后监控到视频完成，下载到 Videos/，用 ffprobe 检查。
6. 如果我要求发布，提交到 LazyEdit 并发布到指定平台。
执行时每一步都验证，不要重复点击生成，不要浪费积分。
```

## Source Repositories and Paths

Keep local paths outside git. From the LazySkills repo, copy the example config,
edit it for the machine, then source it before running command examples:

```bash
cp .config/lazyskills.env.example .config/lazyskills.local.env
$EDITOR .config/lazyskills.local.env
set -a
. .config/lazyskills.local.env
set +a
```

- LALACHAN repo: `$LALACHAN_ROOT`
- Story drafts: `$LALACHAN_ROOT/references/stories`
- Xiaoyunque prompts: `$LALACHAN_ROOT/references/prompts`
- Generated videos: `$LALACHAN_ROOT/Videos`
- LazyEdit repo: `$LAZYEDIT_ROOT`
- LazyEdit API: `$LAZYEDIT_API`
- Nutstore AutoPublish folder: `$NUTSTORE_AUTOPUBLISH`
- Remote AutoPublish queue: `$AUTOPUBLISH_QUEUE_URL`

## Default Characters and Assets

Always upload the actual files. Do not paste local paths into the prompt.

1. `$LALACHAN_ROOT/words-card.jpg`: small white learning card style. Every new episode should use a fresh word matching the story.
2. `$LALACHAN_ROOT/LazyingArtRobot.png`: robot `庄子`; keep the LazyingArt chest logo.
3. `$LALACHAN_ROOT/display.png`: LightMind AI glasses.
4. `$LALACHAN_ROOT/patchwork-leather-notebook-luxury-clean-v2.png`: patchwork notebook/tool prop.
5. `$LALACHAN_ROOT/raraxia.jpeg`: 啦啦侠 individual reference.
6. `$LALACHAN_ROOT/ayachan.png`: 阿芽酱 individual reference.
7. `$LALACHAN_ROOT/sasakun.jpeg`: 飒飒君 individual reference.
8. `$LALACHAN_ROOT/Trio.png`: group identity reference.

Prompt labels must match this order: 图1 to 图8. If fewer images are requested, still keep numbering accurate.

## Story Writing Standard

Write the story first, then the video prompt. The story should be normal human language, not production jargon.

- Use one clear chain: setup, problem, action, twist, payoff.
- Dialogue should sound like friends talking.
- Keep lines short enough for a 15s or 30s video.
- Avoid pseudo-code, abstract slogans, strange translated phrases, and over-explained lore.
- If the story teaches a concept, show it through visible action and one simple sentence.
- For lab or technical scenes, keep the environment believable, clean, and safe.

Save two files:

```bash
references/stories/YYYY-MM-DD-short-slug.md
references/prompts/YYYY-MM-DD-short-slug-15s-seedance-fast.md
```

## Prompt Rules

The prompt should be compact. Overpatched prompts perform worse.

Must include:

- Chinese as the main language.
- Character names: 啦啦侠, 阿芽酱, 飒飒君, 庄子机器人.
- Uploaded image references by 图1, 图2, etc.
- No subtitles: `不要字幕，不要生成任何字幕、说明文字、下三分之一文字或画面文字。`
- Correct visible text only when needed, such as `AgInTi`, `LightMind`, or the learning-card word.

Never include:

- Local paths such as `$HOME/...`
- File names as visible scene text.
- Real platform blockers such as no credits, recharge/payment approval, disabled submit, login, CAPTCHA, or an explicit user budget limit.

## Xiaoyunque Browser Workflow

Use browser UI, not API, unless explicitly requested.

Default:

- Mode: `沉浸式短片`
- Model: relatively cheap suitable Seedance option; prefer Mini体验版/vipnew, otherwise choose a relatively cheaper suitable Fast/Fast VIP/Seedance row
- Duration: `15s` unless user requested 30s or another duration
- Ratio: `4:3`
- Reference source: plus button, upload local images directly; for reference videos use `从资产库选择`

Common commands:

```bash
cd "$LALACHAN_ROOT"
scripts/xyq_cdp_browser.py --cdp-url "$XYQ_CDP_URL" list-pages
scripts/xyq_cdp_browser.py --cdp-url "$XYQ_CDP_URL" bring-to-front PAGE_ID
scripts/xyq_cdp_browser.py --cdp-url "$XYQ_CDP_URL" visible PAGE_ID
```

Upload and verify:

```bash
scripts/xyq_cdp_browser.py --cdp-url "$XYQ_CDP_URL" upload-images-verify PAGE_ID \
  words-card.jpg LazyingArtRobot.png display.png patchwork-leather-notebook-luxury-clean-v2.png \
  raraxia.jpeg ayachan.png sasakun.jpeg Trio.png \
  --timeout 180 \
  --screenshot outputs/xyq-run/after-upload.png
```

Fill the prompt:

```bash
scripts/xyq_cdp_browser.py --cdp-url "$XYQ_CDP_URL" type-prompt PAGE_ID references/prompts/YYYY-MM-DD-short-slug-15s-seedance-fast.md --wait 2
```

Before paid submit, verify:

- The current tab is the correct Xiaoyunque thread.
- Mode, model, duration, ratio, and cost are visible and correct.
- Selected model is a relatively cheap suitable Seedance option; exact cost text is useful but not required if the page allows submission.
- All required uploaded images show success.
- The prompt says no subtitles.
- The submit button is enabled.

If the Xiaoyunque page is stuck on infinite loading, refresh the same tab with `Ctrl+L` then `Enter`, or CDP navigate to the same URL. Do not open a new session unless the current one is unusable.

If a generation fails or asks for continuation, send a short correction in the same thread. Do not start a new thread just to retry.

## Monitor and Download

Use the watcher when possible:

```bash
scripts/xyq_chrome/watch_thread_dom_download.py \
  --cdp-url "$XYQ_CDP_URL" \
  --page-id PAGE_ID \
  --thread-url "THREAD_URL" \
  --output-dir outputs/xyq-run \
  --filename result.mp4 \
  --copy-to Videos \
  --copy-to "$NUTSTORE_AUTOPUBLISH"
```

After download:

```bash
ffprobe -v error -show_entries format=duration -select_streams v:0 -show_entries stream=width,height,codec_name -of json Videos/result.mp4
```

If protected URL download fails, use the page's own `下载` button or browser-context fetch from the logged-in tab. Do not loop external `curl` retries forever.

## LazyEdit Import and Publish

If the user only asks to generate video, import/process but do not publish unless requested. If the user asks to publish, use LazyEdit.

Direct publish for an already imported processed video:

```bash
cd "$LAZYEDIT_ROOT"
source ~/miniconda3/etc/profile.d/conda.sh
conda activate lazyedit
python scripts/lazyedit_publish.py \
  --video-id VIDEO_ID \
  --use-current-settings \
  --platforms shipinhao,youtube,instagram \
  --no-process \
  --guided-monitor \
  --remote-log-command "ssh $AUTOPUBLISH_SSH 'tmux capture-pane -pt autopub:0 -S -140 | tail -n 140'" \
  --wait \
  --poll-seconds 10
```

For a fresh generated video:

```bash
python scripts/lazyedit_publish.py \
  --video "$LALACHAN_ROOT/Videos/VIDEO.mp4" \
  --title TITLE_COMPLETED \
  --use-current-settings \
  --correction-prompt-file "$LALACHAN_ROOT/references/prompts/PROMPT.md" \
  --metadata-prompt-file temp/metadata_brief.md \
  --correct-subtitles \
  --correction-source polished \
  --platforms youtube,instagram \
  --wait \
  --poll-seconds 10
```

Metadata must be short and viewer-facing. Do not dump the whole script into title or description.

Monitor:

```bash
curl -fsS "$LAZYEDIT_API/api/autopublish/queue" | jq '.jobs[:8]'
curl -fsS "$AUTOPUBLISH_QUEUE_URL" | jq '.jobs[-8:]'
ssh "$AUTOPUBLISH_SSH" 'tmux capture-pane -pt autopub:0 -S -120 | tail -n 120'
```

## Completion Report

Report these fields back to the WeChat group or user:

- Story path.
- Prompt path.
- Video path.
- Xiaoyunque mode/model/duration/ratio.
- LazyEdit video id, if imported.
- Publish job id and remote job id, if published.
- Final platform status.
- Any blocker that needs manual login, credit recharge, or page confirmation.

## Critical Caveats

- Do not use Xiaoyunque API unless explicitly requested; the browser UI is cheaper and matches the user's login/credit expectations.
- Do not click submit twice if credits may already be spent.
- Do not create a new Xiaoyunque session unless the current thread is broken.
- Do not skip image upload. Typed paths are not image uploads.
- Prefer Mini体验版/vipnew; if unavailable, use a relatively cheaper suitable Fast/Fast VIP/Seedance option instead of blocking on model selection.
- Default to 15s; use 30s only when requested.
- Default to 4:3 unless requested otherwise.
- Use `AgInTi` capitalization exactly.
