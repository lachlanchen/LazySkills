# LazyEdit Publish Runbook

Date: 2026-06-03

## Systems

- LazyEdit repo: `/home/lachlan/DiskMech/Projects/lazyedit`
- LazyEdit Studio: `http://127.0.0.1:18791/editor`
- LazyEdit API: `http://127.0.0.1:18787`
- CLI: `scripts/lazyedit_publish.py`
- AutoPubMonitor: `/home/lachlan/DiskMech/Projects/autopub-monitor`
- Nutstore import folder: `/home/lachlan/Nutstore Files/AutoPublish/AutoPublish`
- Remote AutoPublish host: `lazyingart`
- Remote AutoPublish repo: `/home/lachlan/Projects/autopub`
- Remote queue API: `http://lazyingart:8081/publish/queue`

## Direct Publish

Use current Studio settings and publish an existing finished output:

```bash
cd /home/lachlan/DiskMech/Projects/lazyedit
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

## AI-Generated Video Publish

Generated video scripts are reference material for subtitle correction. They help infer likely recognition errors, but the final subtitle text should still follow the actual audio and preserve timing. Use a human middle path: do not over-edit, and do not stay too conservative when ASR is obviously abnormal, broken, strange, or mismatched with context. Read neighboring lines, check whether the sentence makes sense, compare with the audio/Whisper text and story context, then infer the most likely intended wording without inventing unsupported content.

Recommended Nutstore import path:

```bash
cp -f /home/lachlan/ProjectsLFS/LALACHAN/Videos/VIDEO.mp4 \
  "/home/lachlan/Nutstore Files/AutoPublish/AutoPublish/VIDEO_COMPLETED.mp4"
tmux capture-pane -pt autopub-monitor:0.1 -S -100 | tail -n 100
tmux capture-pane -pt autopub-monitor:0.2 -S -100 | tail -n 100
curl -fsS http://127.0.0.1:18787/api/videos | jq '.videos[:20] | map({id,title,created_at,file_path})'
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
  --remote-log-command "ssh lachlan@lazyingart 'tmux capture-pane -pt autopub:0 -S -140 | tail -n 140'" \
  --wait \
  --poll-seconds 10
```

If the generated prompt needs stronger instructions, create a temporary context wrapper in the LazyEdit repo `temp/` directory, pass it as `--prompt-file`, then remove it after the run. Do not commit temporary prompt wrappers, ZIPs, generated media, cookies, or logs.

## Monitoring

LazyEdit queue:

```bash
curl -fsS http://127.0.0.1:18787/api/autopublish/queue | jq '.jobs[:8]'
```

Remote queue:

```bash
curl -fsS http://lazyingart:8081/publish/queue | jq '.jobs[:8]'
```

Remote browser logs:

```bash
ssh lachlan@lazyingart 'tmux capture-pane -pt autopub:0 -S -120 | tail -n 120'
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
curl -fsS http://127.0.0.1:18787/api/autopublish/queue | jq '.jobs[:5] | map({id,video_id,status,platforms,remote_status,remote_job_id,error,updated_at})'
curl -fsS http://lazyingart:8081/publish/queue | jq '.jobs[-5:] | map({id,status,platforms,filename,error,updated_at})'
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
  --prompt-file /home/lachlan/ProjectsLFS/LALACHAN/references/prompts/2026-06-03-typhoon-pingpong-shark-duanpian-15s-4x3-budget200.md \
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

- `/home/lachlan/ProjectsLFS/LALACHAN/Videos/firefly_cave_cicada_rain_4x3_15s.mp4`
- Nutstore copy: `/home/lachlan/Nutstore Files/AutoPublish/AutoPublish/firefly_cave_cicada_rain_4x3_15s_COMPLETED.mp4`
- LazyEdit `video_id=352`

Prompt context:

- `/home/lachlan/ProjectsLFS/LALACHAN/references/prompts/2026-06-06-firefly-cave-cicada-rain-duanpian-15s.md`
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
  --remote-log-command "ssh lachlan@lazyingart 'tmux capture-pane -pt autopub:0 -S -140 | tail -n 140'" \
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
