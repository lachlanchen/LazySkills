# LazyEdit Publish Runbook

Date: 2026-06-03

## Systems

Keep local paths outside git. From the LazySkills repo, copy the example config,
edit it for the machine, then source it before running examples:

```bash
cp .config/lazyskills.env.example .config/lazyskills.local.env
$EDITOR .config/lazyskills.local.env
set -a
. .config/lazyskills.local.env
set +a
```

- LazyEdit repo: `$LAZYEDIT_ROOT`
- LazyEdit Studio: `$LAZYEDIT_STUDIO`
- LazyEdit API: `$LAZYEDIT_API`
- CLI: `scripts/lazyedit_publish.py`
- AutoPubMonitor: `$AUTOPUB_MONITOR_ROOT`
- Nutstore import folder: `$NUTSTORE_AUTOPUBLISH`
- Remote AutoPublish host: `$AUTOPUBLISH_SSH`
- Remote AutoPublish repo: `$AUTOPUBLISH_ROOT`
- Remote queue API: `$AUTOPUBLISH_QUEUE_URL`

## Direct Publish

Use current Studio settings and publish an existing finished output:

```bash
cd $LAZYEDIT_ROOT
source ~/miniconda3/etc/profile.d/conda.sh
conda activate lazyedit
python scripts/lazyedit_publish.py \
  --video-id VIDEO_ID \
  --use-current-settings \
  --platforms shipinhao,youtube,instagram \
  --no-process \
  --wait \
  --poll-seconds 10
```

Omit `--no-process` when processing should run before publishing.

## High-Quality Portrait Masters

For vertical shorts made from 4:3 or horizontal generated videos, prefer LazyEdit's built-in portrait blur-fill and normal subtitle/logo reburn. Use a separate high-quality blur-fill master only as a fallback for older runs, layout experiments, or visible quality regressions.

```bash
cd "$LALACHAN_ROOT"
scripts/portrait_blurfill_subtitle_space.sh INPUT.mp4 OUTPUT_portrait_hq.mp4 \
  --fg-y 576 \
  --crf 10 \
  --preset slow \
  --scale-flags lanczos \
  --audio-mode copy
```

For 16:9 MVs converted to `1080x1920`, `--fg-y 576` usually gives the requested top/foreground/bottom balance better than the older `--fg-y 240` layout.

If subtitles should sit mainly in the lower blurred area and the normal LazyEdit burn is too compressed, make an already-burned HQ publish master:

```bash
scripts/hq_subtitle_logo_master.sh OUTPUT_portrait_hq.mp4 corrected.srt OUTPUT_publish_hq.mp4 \
  --logo "$LAZYEDIT_LOGO_PATH" \
  --logo-height 288 \
  --logo-x 38 \
  --logo-y 38 \
  --font-size 44 \
  --margin-v 280 \
  --crf 10 \
  --preset slow \
  --audio-mode copy
```

Then publish with no extra subtitle burn:

```bash
cd "$LAZYEDIT_ROOT"
python scripts/lazyedit_publish.py \
  --video-id VIDEO_ID \
  --use-current-settings \
  --platforms youtube,instagram,shipinhao \
  --metadata-prompt-file temp/metadata_brief.md \
  --no-burn-subtitles \
  --no-process \
  --guided-monitor \
  --wait
```

Check frames before publishing. The MP4 must already contain the configured logo and burned subtitles. Current LALACHAN/MV default logo position is top-right. If the MP4 does not already contain subtitles/logo, use the normal LazyEdit burn flow instead.

## Publish Categories

Use canonical categories in LazyEdit metadata and one-shot publish options:

```text
simplelife
lazyingart
musia
lalachan
lalamv
```

Use `lalamv` for LALACHAN character MVs. Route to YouTube `LalaMV` and Shipinhao `LalaMV` when the platform UI exposes those targets. YouTube playlist selection and Shipinhao collection selection are best effort; do not fail a completed publish only because the category UI is missing or unstable.

## AI-Generated Video Publish

Generated video scripts are reference material for subtitle correction. They help infer likely recognition errors, but the final subtitle text should still follow the actual audio and preserve timing. Use a human middle path: do not over-edit, and do not stay too conservative when ASR is obviously abnormal, broken, strange, or mismatched with context. Read neighboring lines, check whether the sentence makes sense, compare with the audio/Whisper text and story context, then infer the most likely intended wording without inventing unsupported content.

Recommended Nutstore import path:

```bash
cp -f $LALACHAN_ROOT/Videos/VIDEO.mp4 \
  "$NUTSTORE_AUTOPUBLISH/VIDEO_COMPLETED.mp4"
tmux capture-pane -pt autopub-monitor:0.1 -S -100 | tail -n 100
tmux capture-pane -pt autopub-monitor:0.2 -S -100 | tail -n 100
curl -fsS $LAZYEDIT_API/api/videos | jq '.videos[:20] | map({id,title,created_at,file_path})'
```

```bash
python scripts/lazyedit_publish.py \
  --video-id VIDEO_ID \
  --use-current-settings \
  --prompt-file /path/to/generated-script.md \
  --correct-subtitles \
  --correction-source polished \
  --platforms shipinhao,youtube,instagram \
  --guided-monitor \
  --remote-log-command "ssh $AUTOPUBLISH_SSH 'tmux capture-pane -pt autopub:0 -S -140 | tail -n 140'" \
  --wait \
  --poll-seconds 10
```

If the generated prompt needs stronger instructions, create a temporary context wrapper in the LazyEdit repo `temp/` directory, pass it as `--prompt-file`, then remove it after the run. Do not commit temporary prompt wrappers, ZIPs, generated media, cookies, or logs.

## Monitoring

LazyEdit queue:

```bash
curl -fsS $LAZYEDIT_API/api/autopublish/queue | jq '.jobs[:8]'
```

Remote queue:

```bash
curl -fsS $AUTOPUBLISH_QUEUE_URL | jq '.jobs[:8]'
```

Remote browser logs:

```bash
ssh $AUTOPUBLISH_SSH 'tmux capture-pane -pt autopub:0 -S -120 | tail -n 120'
```

AutoPubMonitor panes:

```bash
tmux capture-pane -pt autopub-monitor:0.0 -S -120 | tail -n 120
tmux capture-pane -pt autopub-monitor:0.1 -S -120 | tail -n 120
tmux capture-pane -pt autopub-monitor:0.2 -S -120 | tail -n 120
tmux capture-pane -pt autopub-monitor:0.3 -S -120 | tail -n 120
```

Final evidence checks:

```bash
curl -fsS $LAZYEDIT_API/api/autopublish/queue | jq '.jobs[:5] | map({id,video_id,status,platforms,remote_status,remote_job_id,error,updated_at})'
curl -fsS $AUTOPUBLISH_QUEUE_URL | jq '.jobs[-5:] | map({id,status,platforms,filename,error,updated_at})'
git status --short --untracked-files=no
```

## Verified Typhoon Run

Video:

- `typhoon_pingpong_shark_duanpian_4x3_15s_2026_06_03_22_46_26_COMPLETED`
- LazyEdit `video_id=348`

Command:

```bash
python scripts/lazyedit_publish.py \
  --video-id 348 \
  --use-current-settings \
  --prompt-file $LALACHAN_ROOT/references/prompts/2026-06-03-typhoon-pingpong-shark-duanpian-15s-4x3-budget200.md \
  --correct-subtitles \
  --correction-source polished \
  --platforms shipinhao,youtube,instagram \
  --wait \
  --poll-seconds 10
```

Problem encountered:

- Shipinhao required WeChat Channels login.
- The QR expired once while the user was away.
- The long login wait refreshed the QR and sent a new email.

Resolution:

- Keep the long login wait behavior.
- User scanned/approved login.
- Automation continued and published Shipinhao, Instagram, then YouTube.

Final status:

- LazyEdit job `148`
- Remote job `job-1780500057985-7`
- Platforms: `shipinhao`, `youtube`, `instagram`
- Status: `done`

## Tools Used

- `scripts/lazyedit_publish.py` for CLI/API orchestration.
- `curl` and `jq` for queue APIs.
- `ssh` for Raspberry Pi access.
- `tmux capture-pane` for live process logs.
- `rg` for fast code/log searches on the Pi after installing `ripgrep`.

## Verified Firefly Cave Run

Video:

- `$LALACHAN_ROOT/Videos/firefly_cave_cicada_rain_4x3_15s.mp4`
- Nutstore copy: `$NUTSTORE_AUTOPUBLISH/firefly_cave_cicada_rain_4x3_15s_COMPLETED.mp4`
- LazyEdit `video_id=352`

Prompt context:

- `$LALACHAN_ROOT/references/prompts/2026-06-06-firefly-cave-cicada-rain-duanpian-15s.md`
- A temporary wrapper added correction guardrails: treat the script as story context, use a human middle path between over-editing and under-correcting, fix likely ASR errors, preserve timing/line structure, and generate metadata about a warm fantasy firefly-cave short.

Command pattern:

```bash
python scripts/lazyedit_publish.py \
  --video-id 352 \
  --use-current-settings \
  --prompt-file temp/firefly_cave_publish_context.md \
  --correct-subtitles \
  --correction-source polished \
  --platforms shipinhao,youtube,instagram \
  --guided-monitor \
  --remote-log-command "ssh $AUTOPUBLISH_SSH 'tmux capture-pane -pt autopub:0 -S -140 | tail -n 140'" \
  --wait \
  --poll-seconds 10 \
  --process-timeout 3600 \
  --publish-timeout 7200
```

Observed sequence:

- AutoPubMonitor validated, queued, imported, and removed the Nutstore file from its queue.
- LazyEdit AI subtitle correction saved polished subtitles.
- Pipeline completed translation, subtitle burn, metadata, and cover extraction.
- Shipinhao required QR login, then recovered and published after save-draft/cover-ready checks.
- Instagram published after crop/Next flow.
- YouTube upload completed, title/description were filled from generated metadata, and the final publish completed.

Final status:

- LazyEdit job `154`
- Remote AutoPublish job `job-1780723994544-13`
- Platforms: `shipinhao`, `youtube`, `instagram`
- Status: `done`
