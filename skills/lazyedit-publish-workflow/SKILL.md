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
- For current Musia recording videos, publish with the existing LazyEdit logo at top-right and no LazyEdit subtitles unless the user explicitly asks for subtitles. Use `--no-burn-subtitles --logo --logo-position top-right`, force a fresh logo-only render when the side changes, and inspect a sample frame or the MP4 inside the ZIP before submitting.
- Real publishes should use polished/corrected subtitles and the configured LazyEdit Studio logo unless the user explicitly asks otherwise. Verify logo settings with `curl -fsS $LAZYEDIT_API/api/ui-settings/logo_settings | jq .`; normal logo outputs end in `_subtitles_logo.mp4`.
- For Musia pure-music publishes, lyrics must come from the corrected Musia
  website/publish lyric JSON for the exact selected vocal, not from the original
  prompt lyric, draft lyric, or master-language lyric file. If only a draft is
  available, stop and run the Musia ASR/listening correction workflow before
  creating a Shipinhao Music or YouTube Music package.
- For LALACHAN/RARACHAN generated videos, use the full story/prompt/script for subtitle correction only. Treat it as a reference, not a verbatim transcript: fix clear ASR errors and broken phrases without inventing unsupported dialogue.
- Do not pass a full video script as metadata context. Metadata must be concise and viewer-facing, not a storyboard dump. Prefer `--correction-prompt-file FULL_SCRIPT.md` plus `--metadata-prompt-file temp/METADATA_BRIEF.md`, where the metadata brief contains only hook, characters, tone, payoff, keywords, and platform notes.
- If correction is expected to recover missing generated-video dialogue, inspect `DATA/VIDEO_FOLDER/*_mixed_polished.md` before publish so missed or over-recovered subtitles are caught before any platform post.
- If missing-language recovery creates plain subtitle text, do not restore grammar colors with a per-video patch. Fix or use the shared `lazyedit/subtitle_tokens.py` normalization path so plain text, ruby markup, `word`/`reading` tokens, and speaker-helper rows all render through grammar-typed palette tokens.
- When copying through Nutstore, use one stable `_COMPLETED` filename and watch AutoPubMonitor panes before recopying. Avoid creating duplicate source files just to retrigger the watcher.
- When the source path is already under LazyEdit `DATA/`, use `--video-id` or a non-colliding `--filename`. Do not re-upload `DATA/<stem>/<filename>` with the same filename, because the upload endpoint can truncate the source by writing over it.
- For XiaoHongShu, close hashtag suggestion popovers with Escape/blur before the final publish click. The red publish control may be inside a custom `xhs-publish-btn`, so use the AutoPublish fallback instead of hand-clicking random page coordinates.
- For Douyin, reuse an existing unpublished draft when the upload already exists. Do not use native `send_keys()` for title/description fields or the separate topic widget when debugging; the site can wedge Selenium. Use the AutoPublish JS field replacement path and keep hashtags in the description.
- For Bilibili, optional SMS verification after upload is only for completion notifications; close it and continue. If the page shows `请完成短信验证` while the upload is stuck at `0.0MB/0.0MB`, it is a hard SMS gate, not GeeTest. Click `获取验证码`, get the SMS code from the user, and do not retry upload loops without it. Cover upload is best-effort, so a missing cover dialog should not cause a full reupload.
- If Bilibili shows `0.0MB/0.0MB` and browser-side `preupload` returns code `601` with `您上传视频过快，请您稍作休息后再继续`, stop retrying and wait for cooldown. Repeated upload retries extend the block.
- To add a missing platform to an already-processed LazyEdit output, reuse the existing ZIP if it contains the correct rendered MP4. Re-submit the same ZIP with only the missing platform flags. Repackage only when the existing ZIP points at the wrong output.
- AutoPublish derives the extracted metadata directory from the ZIP filename stem. Do not rename a prepared ZIP to add suffixes like `-topright` unless the internal metadata filename and directory contract are regenerated to match.
- Avoid opening many long-lived terminal monitors. Prefer one `scripts/lazyedit_publish.py --guided-monitor --wait` process plus occasional one-shot queue/tmux checks. Close stale sessions before starting another long publish.

## Setting Semantics

- `--use-current-settings` reads Studio defaults.
- One-shot flags such as `--platforms`, `--languages`, `--subtitle-lift-ratio`, and `--no-burn-subtitles` do not change Studio settings.
- Only `--persist-settings` writes CLI options back to the webapp preferences.
- `--languages` is bottom-to-top subtitle order.
- If Studio logo settings are enabled, `--no-burn-subtitles` still creates a processed logo-only output ending in `_logo.mp4` and publishes that output. Translation is skipped because subtitles are disabled.
- Use polished/corrected subtitles for real publishes and debug publishes unless the user explicitly requests original subtitles.
- Publish category defaults: personal phone/self recordings use `simplelife`; LazyingArt brand/product posts use `lazyingart`; pure music/art-track posts use `musia`; LALACHAN story videos use `lalachan`; LALACHAN character music videos use `lalamv`. Instagram has no stable per-post category/playlist in the desktop web upload flow, so AutoPublish only logs the inferred category there and uses normal captions/tags. LazyEdit metadata generation asks the model for `publish_category` (`simplelife`, `lazyingart`, `musia`, `lalachan`, or `lalamv`) and the router falls back to source-path/keyword inference. `music` is only a backwards-compatible alias for `musia`. Use `--publish-category lalamv`, `--youtube-playlist LalaMV`, or `--shipinhao-collection LalaMV` for MV overrides.
- Burn the existing LazyEdit webapp logo on real publishes unless the user explicitly says no logo. Use the configured Studio logo; do not upload or invent a new asset.
- Required logo state is `enabled: true`, `logoPath` present, and the requested position set. Current Musia/LALACHAN/MV default is `position: "top-right"`. Check it before CLI/API publishes with `curl -fsS $LAZYEDIT_API/api/ui-settings/logo_settings | jq .`. For no-subtitle logo-only publishes, force a fresh burn when the position changes, extract a sample frame with `ffmpeg`, and visually verify the logo side before submitting to AutoPublish.
- `--no-process` reuses an already completed output. Use it when the user says "last run", "same version", or "already finished run".
- `--publication-session-id ID` targets a specific run. Omit it for the current output.

## 2026-06-30 Musia/Platform Runbook

See `$LAZYEDIT_ROOT/references/PUBLISH_RUNBOOK_MUSIA_AND_PLATFORM_SMOOTHING_2026_06_30.md` for the full incident record. Key rules:

- Confirm the MP4 inside the ZIP is the desired version before real publish.
- Musia recordings: no LazyEdit subtitles by default; top-right logo; category `musia`; use curated song context for metadata.
- LALACHAN/generated story videos: use the full script for subtitle correction, but use a short metadata brief so public descriptions do not become storyboard dumps.
- Shipinhao collection and YouTube playlist selection are best-effort; if the requested collection/playlist is absent or not immediately selectable, publish and report the fallback.
- Douyin should reuse drafts and use the JS field replacement path.
- Xiaohongshu needs popovers closed before final publish.
- Bilibili upload cooldown/SMS gates should stop retries; do not solve SMS gates with GeeTest/Tuling.
- Shipinhao Music: publish as music/song, not album; use square covers; confirm cover overlays; fill lyrics, story/`音乐人说`, language, genre, author, originality/agreement when visible; use corrected Musia website vocal JSON for the exact selected audio. Before posting, inspect `*_lyrics.txt` in the package and compare it with `website/data/songs/<song>/lyrics/<vocal>/<lang>.json`, not the original prompt lyric or another vocal's translation JSON. If the live language dropdown lacks English/Japanese, publish and report the fallback instead of silently claiming it was selected.

## Category Cleanup

Use platform cleanup scripts only after an inventory or dry run. They attach to
the logged-in browser sessions and are read-only until `--apply`.

Shipinhao collections:

```bash
ssh lachlan@lazyingart 'cd ~/Projects/autopub && /home/lachlan/venvs/autopub/bin/python scripts/manage_shipinhao_videos.py ensure-collection --collection LalaMV --apply'
ssh lachlan@lazyingart 'cd ~/Projects/autopub && /home/lachlan/venvs/autopub/bin/python scripts/manage_shipinhao_videos.py ensure-collection --collection Musia --apply'
ssh lachlan@lazyingart 'cd ~/Projects/autopub && /home/lachlan/venvs/autopub/bin/python scripts/manage_shipinhao_videos.py ensure-collection --collection 啦啦侠 --apply'
ssh lachlan@lazyingart 'cd ~/Projects/autopub && /home/lachlan/venvs/autopub/bin/python scripts/manage_shipinhao_videos.py inventory --scrolls 5 --output /tmp/shipinhao_inventory.json'
ssh lachlan@lazyingart 'cd ~/Projects/autopub && /home/lachlan/venvs/autopub/bin/python scripts/manage_shipinhao_videos.py move-category --category lalamv --lalamv-collection LalaMV --scrolls 5 --output /tmp/shipinhao_lalamv_plan.json'
ssh lachlan@lazyingart 'cd ~/Projects/autopub && /home/lachlan/venvs/autopub/bin/python scripts/manage_shipinhao_videos.py move-classified --scrolls 5 --output /tmp/shipinhao_move_plan.json'
```

Apply in small batches or by exact visible title fragment:

```bash
ssh lachlan@lazyingart 'cd ~/Projects/autopub && /home/lachlan/venvs/autopub/bin/python scripts/manage_shipinhao_videos.py move --query "visible title fragment" --collection 啦啦侠 --apply'
```

Shipinhao mirrored metadata/description management:

```bash
python AutoPublish/scripts/shipinhao_mirror_manager.py export-metadata --metadata-root DATA --days 45 --output /tmp/lazyedit_shipinhao_metadata_index.json
python AutoPublish/scripts/shipinhao_mirror_manager.py export-publish-history --limit 500 --output /tmp/lazyedit_shipinhao_publish_history.json
ssh lachlan@lazyingart 'cd ~/Projects/autopub && /home/lachlan/venvs/autopub/bin/python scripts/shipinhao_mirror_manager.py mirror --scrolls 5 --output /tmp/shipinhao_mirror.json'
python AutoPublish/scripts/shipinhao_mirror_manager.py sync-db --db /tmp/shipinhao_management.sqlite --mirror /tmp/shipinhao_mirror.json --metadata-index /tmp/lazyedit_shipinhao_metadata_index.json --publish-history /tmp/lazyedit_shipinhao_publish_history.json --output-plan /tmp/shipinhao_description_plan.json
python AutoPublish/scripts/shipinhao_mirror_manager.py db-report --db /tmp/shipinhao_management.sqlite --limit 20
```

Use this mirror manager for existing-post control, not publication. On
2026-06-29, old date-only rows could be matched back to LazyEdit metadata, but
Shipinhao's `修改描述和封面` page only allowed modifying selected existing text
with a 20-character limit. Blank/missing descriptions could not be restored
through the visible desktop UI; the tool reports
`unsupported-description-repair` for that state and records apply attempts in
the SQLite mirror DB. Inspect every JSON plan before `--apply`.

YouTube playlists:

```bash
ssh lachlan@lazyingart 'cd ~/Projects/autopub && /home/lachlan/venvs/autopub/bin/python scripts/manage_y2b_videos.py move-category --category lalamv --lalamv-playlist LalaMV --scrolls 20 --output /tmp/youtube_lalamv_plan.json'
ssh lachlan@lazyingart 'cd ~/Projects/autopub && /home/lachlan/venvs/autopub/bin/python scripts/manage_y2b_videos.py move-classified --scrolls 20 --output /tmp/youtube_move_plan.json'
```

For `lalamv`, target YouTube playlist `LalaMV`. Playlist selection and creation are best effort: if YouTube creates the playlist but does not expose it immediately for selection, continue the publish and report the limitation instead of failing the whole job.

Instagram:

Instagram does not have a comparable per-post category/playlist/collection
target in the current desktop web upload flow. Do not run an Instagram
category backfill. Keep using metadata category for YouTube/Shipinhao routing
and normal Instagram caption/tags.

Never bulk-apply a generated plan without inspecting the JSON. If the page is
logged out, wrong, or the visible row text is weak, stop and open the correct
management page in the browser first.

## Quality-Preserving Portrait Publish Masters

When a 4:3 or horizontal generated video is converted to vertical mobile format, do not accept visible quality loss from repeated normal delivery encodes. Keep the foreground sharp, use a blurred current-frame fill, and leave the lower blurred area for subtitles.

Preferred current path: use LazyEdit's built-in portrait blur-fill feature and normal subtitle/logo reburn. In LALACHAN mode, LazyEdit targets a lower blurred reserve of about 40% (`bottomSpaceRatio=0.4`) and derives the top margin from the source aspect ratio. Manual blur-fill scripts are fallback/recovery tools for layout experiments or older runs.

Recommended portable pattern from the LALACHAN repo:

```bash
cd "$LALACHAN_ROOT"

scripts/portrait_blurfill_subtitle_space.sh INPUT.mp4 OUTPUT_portrait_hq.mp4 \
  --fg-y 544 \
  --crf 10 \
  --preset slow \
  --scale-flags lanczos \
  --audio-mode copy
```

For `1080x1920` portrait output from a 16:9 MV, the built-in `bottomSpaceRatio=0.4` layout is preferred. If falling back to the manual script, `--fg-y 544` roughly matches the same lower-space target for 16:9 material; avoid the older high-foreground `--fg-y 240` unless deliberately reserving a much larger lower area.

In the LazyEdit Publish tab, use the `Calculated layout` card and `View layout`
modal to inspect source-specific top/foreground/bottom geometry before
processing.

If LazyEdit's normal subtitle/logo burn visibly reduces quality, create an already-burned high-quality publish master locally. Keep the normal configured logo position and style, usually top-right for current LALACHAN/MV work, and place subtitles mostly in the lower blur area:

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

Then import/publish `OUTPUT_publish_hq.mp4` with `--no-burn-subtitles`. This avoids a second burn/re-encode because the MP4 already includes the normal logo and burned subtitles:

```bash
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

Use this path only after verifying sample frames prove the subtitles and logo are already present in the MP4. If they are not present, use the normal LazyEdit burn path.

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

Create a no-subtitle video while keeping the configured Studio logo:

```bash
python scripts/lazyedit_publish.py --video-id VIDEO_ID --use-current-settings --no-burn-subtitles --platforms youtube,instagram --wait
```

Pure music/audio packaging should go through LazyEdit first, mirroring the
video ZIP contract. LazyEdit creates the metadata, lyrics, audio copy, YouTube
art-track MP4, manifest, original-proof ZIP, and cover candidates; AutoPublish
only consumes the ZIP with `publish_shipinhao_music=true` and/or
`publish_youtube_music=true`.

For Musia songs, `--lyrics-json` is a publication-critical field. Point it to
the final corrected website lyric JSON for the selected audio asset, for
example:

```text
/home/lachlan/ProjectsLFS/Musia/website/data/songs/<media-id>/lyrics/<vocal-set>/<active-lang>.json
```

Do not pass `lyrics.txt`, prompt drafts, planning translations, or a companion
language's JSON unless that exact file was corrected against the selected vocal.
If the music package lyrics disagree with `fun.lazying.art`, rebuild the package
before publishing. Shipinhao Music should display the same corrected lyrics as
the website for that vocal.

```bash
python scripts/lazyedit_music_package.py \
  --audio /path/to/song.mp3 \
  --title "Song Title" \
  --author "Musia 慕莎" \
  --language 中文 \
  --genre Pop \
  --story "Short music story for 音乐人说." \
  --lyrics-json /path/to/musia/lyrics/mixed-vocal/mul.json \
  --cover /path/to/artwork.png \
  --cover-video /path/to/related-video.mp4 \
  --cover-count 9 \
  --cover-model aginti+codex \
  --aginti-cover-count 5 \
  --codex-cover-count 4 \
  --proof /path/to/website/manifest.json \
  --source-url "https://fun.lazying.art/#song-id" \
  --output-slug song-title-music \
  --platforms shipinhao_music,youtube_music \
  --autopublish-url http://lazyingart:8081
```

The equivalent API is:

```bash
curl -fsS http://127.0.0.1:18787/api/music/package \
  -H 'Content-Type: application/json' \
  -d '{
    "audio": "/path/to/song.mp3",
    "title": "Song Title",
    "author": "Musia 慕莎",
    "language": "中文",
    "lyrics_json": "/path/to/lyrics.json",
    "cover": "/path/to/artwork.png",
    "cover_video": "/path/to/related-video.mp4",
    "cover_count": 9,
    "cover_model": "aginti+codex",
    "aginti_cover_count": 5,
    "codex_cover_count": 4,
    "source_url": "https://fun.lazying.art/#song-id",
    "slug": "song-title-music",
    "platforms": {"shipinhao_music": true, "youtube_music": true}
  }'
```

Set `--post` or JSON `"post": true` only after inspecting the package. As of
2026-06-29, the verified desktop creation route is:

```text
https://channels.weixin.qq.com/platform/post/createMusic
```

The management/sidebar route is:

```text
https://channels.weixin.qq.com/platform/post/music
```

Shipinhao currently has no verified standalone desktop `发表专辑` route. Album
(`专辑`) is handled as required metadata inside the `发表音乐` song form, and
also appears as a read-only management tab. Use AutoPublish
`pub_shipinhao_music.py` for song creation and `pub_shipinhao_zhuanji.py` for
read-only album/music tab inspection:

```bash
ssh lachlan@lazyingart 'cd ~/Projects/autopub && /home/lachlan/venvs/autopub/bin/python pub_shipinhao_zhuanji.py'
```

The zhuanji helper saves `logs/shipinhao-zhuanji-management.json`. Do not
represent a click on `发表音乐` as final listing proof unless the management tab
or backend status shows a row.

After the account has at least one album, the music form may show only
`专辑信息 / 选择专辑 / 请选择专辑`. The publisher must switch the Vue album
component to `新建专辑` before filling `专辑名称`, cover, and intro; otherwise
`发表音乐` stays disabled. Verified on 2026-06-29: management showed two albums
and two music rows after publishing `One Sky, Three Lights` and
`アヤちゃん 光の雨`.

Do not claim `音乐人说`, `歌曲简介`, `歌曲故事`, or a video-style `声明原创`
was filled unless the live create form exposes those fields. In the verified
2026-06-29 run, the story text existed in package metadata and album intro, but
the separate `音乐人说` field was not present; `作品类型` stayed on the page
default `原创`, and original proof was uploaded through `证明文件`.

Shipinhao music rejects MP3 files below 256kbps. LazyEdit now transcodes low
bitrate MP3 inputs to a package-local `*_shipinhao_320k.mp3` copy. Verify with
`ffprobe` if a package fails to enable the submit button. Required fields filled
by AutoPublish include title, lyrics, author, singer, lyricist, composer,
producer, album name, album description, album cover, original-proof ZIP, and
the `我已阅读《视频号音乐人发表须知》` checkbox.
Shipinhao's `歌曲曲风` dropdown uses Chinese site labels. AutoPublish maps
common English genres such as `Bedroom Pop`, `lofi`, and `pop` to `流行`; if a
new English genre times out, add it to `pub_shipinhao_music.py` instead of
editing the package by hand.

YouTube Music in this workflow means public YouTube Studio upload of a generated
music art-track video. LazyEdit writes `youtube_music_video_filename` and
`video_filename` to metadata, and AutoPublish `pub_y2b_music.py` uploads that
H.264/AAC MP4 with the cover thumbnail, title, description/story, lyrics, tags,
and `Musia` playlist when available. Direct YouTube Music audio upload is a
personal library feature, so do not claim it as public YouTube Music
distribution.

Music package records are durable in LazyEdit:

```bash
python scripts/lazyedit_music_records.py list --limit 20
python scripts/lazyedit_music_records.py update ID --shipinhao-item-url URL
python scripts/lazyedit_music_records.py update ID --deleted
```

When cover art is not fully prepared, pass one curated cover plus
`--cover-video` and `--cover-count 9`; LazyEdit will extract enough frame covers
to fill the nine-background-image package. If AgInTi generates better covers,
pass those as repeated `--cover` arguments instead.

## LALACHAN / AI-Generated Video

Default post-generation rule: when a LALACHAN/Xiaoyunque video has finished,
auto-download it, verify duration/size with `ffprobe`, copy it to
`$LALACHAN_ROOT/Videos`, and send the verified MP4 back to the requesting chat.
Submit to LazyEdit only when the current user request explicitly asks for
LazyEdit/import/process or public publishing. For a LazyEdit-only request, use
direct CLI upload with `--no-publish`; Nutstore AutoPublish import is an
acceptable fallback. For a public publish request, run the normal LazyEdit
publish workflow exactly once for the requested platforms.

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
