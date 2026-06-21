---
name: lazyedit-publish-workflow
description: Use when publishing videos through LazyEdit, AutoPubMonitor, a remote AutoPublish host, Shipinhao, YouTube, Instagram, or LALACHAN-generated videos; covers direct CLI/API publishing, current-run reuse, one-shot settings overrides, subtitle correction prompts, Nutstore AutoPublish import, and monitoring/debugging the distributed publish workflow.
---

# LazyEdit Publish Workflow

Use this skill for normal LazyEdit publish tasks and for AI-generated videos from LALACHAN/RARACHAN that need subtitle correction, processing, and platform publishing.

## Runtime Map

- LazyEdit repo/backend: `$LAZYEDIT_ROOT`
- Studio app: `$LAZYEDIT_STUDIO`
- LazyEdit API: `$LAZYEDIT_API`
- Publish CLI: `scripts/lazyedit_publish.py`
- AutoPubMonitor repo: `$AUTOPUB_MONITOR_ROOT`
- Nutstore import folder: `$NUTSTORE_AUTOPUBLISH`
- Remote AutoPublish host: `ssh $AUTOPUBLISH_SSH`
- Remote AutoPublish repo: `$AUTOPUBLISH_ROOT`
- Remote publish API: `$AUTOPUBLISH_API`
- Remote tmux session: `autopub`

Keep local paths outside git. From the LazySkills repo, copy the example config,
edit it for the machine, then source it before using command examples:

```bash
cp .config/lazyskills.env.example .config/lazyskills.local.env
$EDITOR .config/lazyskills.local.env
set -a
. .config/lazyskills.local.env
set +a
```

## Core Rule

Prefer the LazyEdit CLI over manual browser work. It creates normal LazyEdit jobs, so the webapp queue stays in sync.

Activate the environment first:

```bash
cd "$LAZYEDIT_ROOT"
source ~/miniconda3/etc/profile.d/conda.sh
conda activate lazyedit
```

## Safety Rules

- Do not publish to real platforms just to debug packaging, subtitles, or logo output. Use `--no-publish` first, inspect the generated ZIP/final MP4, then publish exactly once when the package is correct.
- Real publishes should use polished/corrected subtitles and the configured LazyEdit Studio logo unless the user explicitly asks otherwise. Verify logo settings with `curl -fsS $LAZYEDIT_API/api/ui-settings/logo_settings | jq .`; normal logo outputs end in `_subtitles_logo.mp4`.
- For LALACHAN/RARACHAN generated videos, use the full story/prompt/script for subtitle correction only. Treat it as a reference, not a verbatim transcript: fix clear ASR errors and broken phrases without inventing unsupported dialogue.
- Do not pass a full video script as metadata context. Metadata must be concise and viewer-facing, not a storyboard dump. Prefer `--correction-prompt-file FULL_SCRIPT.md` plus `--metadata-prompt-file temp/METADATA_BRIEF.md`, where the metadata brief contains only hook, characters, tone, payoff, keywords, and platform notes.
- If correction is expected to recover missing generated-video dialogue, inspect `DATA/VIDEO_FOLDER/*_mixed_polished.md` before publish so missed or over-recovered subtitles are caught before any platform post.
- If missing-language recovery creates plain subtitle text, do not restore grammar colors with a per-video patch. Fix or use the shared `lazyedit/subtitle_tokens.py` normalization path so plain text, ruby markup, `word`/`reading` tokens, and speaker-helper rows all render through grammar-typed palette tokens.
- When copying through Nutstore, use one stable `_COMPLETED` filename and watch AutoPubMonitor panes before recopying. Avoid creating duplicate source files just to retrigger the watcher.

## Setting Semantics

- `--use-current-settings` reads Studio defaults.
- One-shot flags such as `--platforms`, `--languages`, `--subtitle-lift-ratio`, and `--no-burn-subtitles` do not change Studio settings.
- Only `--persist-settings` writes CLI options back to the webapp preferences.
- `--languages` is bottom-to-top subtitle order.
- Use polished/corrected subtitles for real publishes and debug publishes unless the user explicitly requests original subtitles.
- Burn the existing LazyEdit webapp logo on real publishes unless the user explicitly says no logo. Use the configured Studio logo; do not upload or invent a new asset.
- Required logo state is `enabled: true`, `logoPath` present, and `position: "top-left"`. Check it before CLI/API publishes with `curl -fsS $LAZYEDIT_API/api/ui-settings/logo_settings | jq .`.
- `--no-process` reuses an already completed output. Use it when the user says "last run", "same version", or "already finished run".
- `--publication-session-id ID` targets a specific run. Omit it for the current output.

## Common Commands

Process with separate subtitle-correction and metadata context, then publish:

```bash
python scripts/lazyedit_publish.py \
  --video-id VIDEO_ID \
  --use-current-settings \
  --correction-prompt-file $LALACHAN_ROOT/references/prompts/FULL_SCRIPT.md \
  --metadata-prompt-file temp/metadata_brief.md \
  --no-correct-subtitles \
  --steps keyframes,caption,transcribe,polish,translate,burn,metadata_zh,metadata_en,cover \
  --platforms shipinhao,youtube,instagram \
  --guided-monitor \
  --remote-log-command "ssh $AUTOPUBLISH_SSH 'tmux capture-pane -pt autopub:0 -S -140 | tail -n 140'" \
  --wait \
  --poll-seconds 10 \
  --process-timeout 3600 \
  --publish-timeout 7200
```

Use this for existing videos with no subtitles yet when the user provides background context. The full script is passed as `polish_notes`; the short metadata brief is passed as metadata notes. Do not reuse the full script as the metadata file. Delete temporary metadata briefs after the run unless the user asks to preserve them.

Publish an already finished output:

```bash
python scripts/lazyedit_publish.py \
  --video-id VIDEO_ID \
  --use-current-settings \
  --platforms shipinhao,youtube,instagram \
  --no-process \
  --wait \
  --poll-seconds 10
```

Publish only YouTube and Instagram:

```bash
python scripts/lazyedit_publish.py --video-id VIDEO_ID --use-current-settings --platforms youtube,instagram --no-process --wait --poll-seconds 10
```

Publish only Shipinhao:

```bash
python scripts/lazyedit_publish.py --video-id VIDEO_ID --use-current-settings --platforms shipinhao --no-process --wait --poll-seconds 10
```

Process then publish:

```bash
python scripts/lazyedit_publish.py --video-id VIDEO_ID --use-current-settings --platforms youtube,instagram --wait --poll-seconds 10
```

Process/publish with lightweight guided monitoring:

```bash
python scripts/lazyedit_publish.py \
  --video-id VIDEO_ID \
  --use-current-settings \
  --platforms youtube,instagram \
  --guided-monitor \
  --remote-log-command "ssh $AUTOPUBLISH_SSH 'tmux capture-pane -pt autopub:0 -S -80 | tail -n 80'" \
  --wait \
  --poll-seconds 10
```

Use `--guided-monitor` when the user wants less manual supervision. It prints heartbeat progress during blocking subtitle correction, follows the local LazyEdit queue, checks the remote AutoPublish queue, and can periodically tail the Pi `autopub` tmux log. It should not restart services by itself; diagnose first, then intervene only when the queue reports failure or the logs show a clear stall.

If a processed output includes subtitles, confirm the final video path or subtitle-burn config has the logo overlay applied. Normal logo outputs end in `_subtitles_logo.mp4`.

Override languages for one run without changing Studio defaults:

```bash
python scripts/lazyedit_publish.py --video-id VIDEO_ID --use-current-settings --languages zh-Hant,ja,en --platforms youtube,instagram --wait
```

## LALACHAN / AI-Generated Video

Default post-generation rule: when a LALACHAN/Xiaoyunque video has finished,
auto-download it, verify duration/size with `ffprobe`, copy it to
`$LALACHAN_ROOT/Videos`, and submit it to LazyEdit. Direct
CLI upload is preferred; Nutstore AutoPublish import is acceptable. If the user
did not explicitly request real platform publishing, pass `--no-publish` so the
video is imported and processed in LazyEdit but not posted.

If a generated video should go through the normal import path, copy it to Nutstore with a stable `_COMPLETED` name:

```bash
cp -f $LALACHAN_ROOT/Videos/VIDEO.mp4 \
  "$NUTSTORE_AUTOPUBLISH/VIDEO_COMPLETED.mp4"
```

Then watch AutoPubMonitor and find the imported LazyEdit video id:

```bash
tmux capture-pane -pt autopub-monitor:0.1 -S -100 | tail -n 100
tmux capture-pane -pt autopub-monitor:0.2 -S -100 | tail -n 100
curl -fsS $LAZYEDIT_API/api/videos | jq '.videos[:20] | map({id,title,created_at,file_path})'
```

For direct upload with correction and a concise metadata brief:

```bash
python scripts/lazyedit_publish.py \
  --video $LALACHAN_ROOT/Videos/VIDEO.mp4 \
  --title TITLE_COMPLETED \
  --use-current-settings \
  --correction-prompt-file $LALACHAN_ROOT/references/prompts/PROMPT.md \
  --metadata-prompt-file temp/metadata_brief.md \
  --correct-subtitles \
  --correction-source polished \
  --platforms shipinhao,youtube,instagram \
  --wait \
  --poll-seconds 10
```

Use the LALACHAN story/prompt/script as subtitle-correction background. For subtitle correction, treat the script as a reference, not a verbatim source. Use a human middle path: do not over-edit, and do not stay too conservative when the ASR is obviously abnormal, broken, or mismatched with the context. Read neighboring lines, check whether the sentence makes sense, compare it with the audio/Whisper text and the story context, then infer the most likely intended wording. Fix recognition errors, names, objects, and broken phrases while preserving timing and line structure where possible. The final corrected subtitles do not need to be identical to the script if the audio or generated video differs, and they should not invent unsupported content.

For metadata, write a short temporary brief before running the CLI. Include hook, characters, setting, central joke or emotion, final payoff, and 8 to 15 keywords/hashtags. Add the explicit instruction: do not reveal every scene beat or line of dialogue.

If the correction prompt needs extra guardrails, create a temporary correction wrapper in `temp/` and pass it as `--correction-prompt-file`. If metadata needs guardrails, create a temporary metadata brief and pass it as `--metadata-prompt-file`. Avoid `--prompt-file` for full generated-video scripts because it feeds the same long text to both subtitle correction and metadata. Do not commit temporary prompt wrappers, generated ZIPs, or runtime media.

If the user requests no rerun, use `--no-process`.

## Manual Subtitle Quality Pass

After transcription/polish, inspect the polished subtitles before publish when the user gave precise context:

```bash
sed -n '1,180p' DATA/VIDEO_FOLDER/*_mixed_polished.md
rg -n "bad term|broken term|ASR artifact" DATA/VIDEO_FOLDER/*_mixed_polished.*
```

Use a middle path:

- Fix clear recognition errors, broken filler words, wrong objects, and wrong names.
- Keep the conversational structure and timing.
- Do not invent lines that are unsupported by the transcript/context.
- If the corrected text is Chinese filler such as `嗯` or `呃...`, make sure the JSON item language is `zh`, not a stale `ja` or `en`.

When hand-editing subtitles, keep `.json`, `.srt`, and `.md` aligned. Prefer the LazyEdit subtitle-correction save endpoint if it responds quickly. If it starts a duplicate transcription or times out, stop that duplicate process and use the DB recovery note below.

## Recovery Notes

A late duplicate Whisper run can write a newer failed `mixed` transcription row after a valid completed transcript already exists. Symptoms:

- `process-status` shows `transcribe:error`.
- Corrected `*_mixed_polished.json/.srt/.md` files exist and downstream steps may already be done.
- A stray process like `vad_lang_subtitle.py ... --force` or `HandBrakeCLI ... _compatible.MOV` is visible in `ps`.

First stop only the duplicate worker if it is clearly redundant:

```bash
ps -eo pid,ppid,cmd | rg 'vad_lang_subtitle|HandBrakeCLI|scripts/lazyedit_publish.py'
kill PID
```

Then insert a fresh completed `mixed` row pointing at the verified corrected files so status ordering recovers:

```bash
source .env 2>/dev/null || true
psql "${LAZYEDIT_DATABASE_URL:-${DATABASE_URL:-dbname=lazyedit_db}}" -v ON_ERROR_STOP=1 -c "
INSERT INTO transcriptions (
  video_id, language_code, status,
  output_json_path, output_srt_path, output_md_path,
  error, publication_session_id
) VALUES (
  VIDEO_ID, 'mixed', 'completed',
  '/abs/path/to/VIDEO_compatible_mixed_polished.json',
  '/abs/path/to/VIDEO_compatible_mixed_polished.srt',
  '/abs/path/to/VIDEO_compatible_mixed_polished.md',
  NULL, NULL
);"
```

This is a narrow status repair, not a content rewrite. Confirm with:

```bash
psql "${LAZYEDIT_DATABASE_URL:-${DATABASE_URL:-dbname=lazyedit_db}}" -P pager=off -c \
  "SELECT id, language_code, status, output_json_path, error, created_at
   FROM transcriptions WHERE video_id=VIDEO_ID ORDER BY id DESC LIMIT 8;"
```

If all downstream outputs exist except cover, extract cover directly:

```bash
curl -m 180 -fsS -H 'Content-Type: application/json' \
  -d '{"lang":"zh"}' \
  $LAZYEDIT_API/api/videos/VIDEO_ID/cover | jq .
```

Then publish without rerunning processing or correction:

```bash
python scripts/lazyedit_publish.py \
  --video-id VIDEO_ID \
  --use-current-settings \
  --no-correct-subtitles \
  --no-process \
  --platforms shipinhao,youtube,instagram \
  --guided-monitor \
  --remote-log-command "ssh $AUTOPUBLISH_SSH 'tmux capture-pane -pt autopub:0 -S -140 | tail -n 140'" \
  --wait \
  --poll-seconds 10
```

## Local Section Clip Publishing

Use this path when another workflow has already created a finished section clip, such as a transcript-derived split from Audio2Text. Publish the section clip directly; do not re-split or regenerate the source video.

Before publishing, gather:

- Absolute clip path.
- Suggested title from the section JSON or manifest.
- Section time range.
- Full transcript path, if subtitle correction or metadata needs context.
- Split manifest path, if the user asks what the clip came from.

Example direct publish for a local section clip:

```bash
python scripts/lazyedit_publish.py \
  --video /path/to/video.mp4 \
  --title "Detection, decision making, and automated data generation" \
  --use-current-settings \
  --platforms shipinhao,youtube,instagram \
  --wait \
  --poll-seconds 10
```

If subtitles or metadata should use transcript context, create short temporary context files from the transcript and section notes. Pass subtitle context with `--correction-prompt-file` and public-facing metadata context with `--metadata-prompt-file`. Remove temporary files after the run unless the user asks to keep them.

For section clips generated from a private source, public metadata should describe only the section content. Do not mention the source recording, private processing notes, or agent workflow unless the user explicitly asks.

## Monitoring

Local LazyEdit queue:

```bash
curl -fsS $LAZYEDIT_API/api/autopublish/queue | jq '.jobs[:8]'
```

Remote AutoPublish queue:

```bash
curl -fsS $AUTOPUBLISH_QUEUE_URL | jq '.jobs[:8]'
```

Remote browser automation:

```bash
ssh $AUTOPUBLISH_SSH 'tmux capture-pane -pt autopub:0 -S -120 | tail -n 120'
```

AutoPubMonitor import/session:

```bash
tmux capture-pane -pt autopub-monitor:0.0 -S -120 | tail -n 120
tmux capture-pane -pt autopub-monitor:0.1 -S -120 | tail -n 120
tmux capture-pane -pt autopub-monitor:0.2 -S -120 | tail -n 120
tmux capture-pane -pt autopub-monitor:0.3 -S -120 | tail -n 120
```

## Shipinhao Notes

- Shipinhao may require a WeChat QR/login email. Keep monitoring after the user scans.
- Keep the long login wait behavior. It is intentional and useful when the user is away or misses the first QR.
- The automation should wait for upload completion, cover readiness, save draft, then publish.
- Current UI may not expose short title or cover upload; skip those if absent.
- Expected successful log includes `Successfully published on ShiPinHao.`

## AutoPubMonitor Notes

- Nutstore files copied into `$NUTSTORE_AUTOPUBLISH` are synced/imported by AutoPubMonitor.
- If a file is renamed while monitor is active, check the tmux panes and queue file before assuming it imported.
- If LazyEdit is down, AutoPubMonitor wrapper must preserve nonzero exit codes so queued files are not silently dropped.

## Handoff Checks

Before final response, verify:

```bash
curl -fsS $LAZYEDIT_API/api/autopublish/queue | jq '.jobs[:8] | map({id,video_id,status,platforms,remote_status,remote_job_id,error})'
curl -fsS $AUTOPUBLISH_QUEUE_URL | jq '.jobs[:8] | map({id,status,platforms,filename,error,updated_at})'
```

Report the LazyEdit job id, remote job id, platforms, status, and whether processing was reused or rerun.

## Verified Run: 2026-06-03 Typhoon Ping Pong Shark

Request:

- Publish `typhoon_pingpong_shark_duanpian_4x3_15s_2026_06_03_22_46_26_COMPLETED` as before.
- Use generated-video subtitle correction from the LALACHAN prompt/script.

Method:

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

What happened:

- LazyEdit had already imported the Nutstore file as `video_id=348`.
- AI subtitle correction saved polished subtitles before processing.
- Processing completed: transcribe, translate, burn, metadata, cover.
- Shipinhao blocked on login until the user scanned the emailed QR.
- The QR expired once; the existing long wait refreshed it and sent a new email.
- After login, Shipinhao published, then Instagram published, then YouTube published.

Tools used:

- `scripts/lazyedit_publish.py` for API/CLI orchestration.
- `curl` + `jq` for LazyEdit and remote AutoPublish queue checks.
- `ssh $AUTOPUBLISH_SSH` and `tmux capture-pane -pt autopub:0` for remote browser automation logs.
- `tmux capture-pane -pt autopub-monitor:*` for Nutstore/import checks.
- `rg` on the Pi after installing `ripgrep` for faster code/log searches.

Final result:

- LazyEdit job `148`
- Remote job `job-1780500057985-7`
- Platforms `shipinhao`, `youtube`, `instagram`
- Status `done`

## Verified Run: 2026-06-06 Firefly Cave

Request:

- Copy `$LALACHAN_ROOT/Videos/firefly_cave_cicada_rain_4x3_15s.mp4` to Nutstore.
- Use `$LALACHAN_ROOT/references/prompts/2026-06-06-firefly-cave-cicada-rain-duanpian-15s.md` as subtitle/metadata context.
- Publish to `shipinhao`, `youtube`, and `instagram`.

Method:

```bash
cp -f $LALACHAN_ROOT/Videos/firefly_cave_cicada_rain_4x3_15s.mp4 \
  "$NUTSTORE_AUTOPUBLISH/firefly_cave_cicada_rain_4x3_15s_COMPLETED.mp4"

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

What happened:

- AutoPubMonitor imported the Nutstore file as `video_id=352`.
- AI correction saved polished subtitles first.
- Processing completed translation, burn, metadata, and cover.
- Shipinhao required QR login, recovered after login, saved draft, waited for cover readiness, and published.
- Instagram published after crop/Next; YouTube uploaded, filled title/description from metadata, and published.

Final result:

- LazyEdit job `154`
- Remote job `job-1780723994544-13`
- Platforms `shipinhao`, `youtube`, `instagram`
- Status `done`
