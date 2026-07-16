# Lala Studio End-to-End Runbook

Use this reference when one request spans story writing, words-card generation,
Xiaoyunque video production, safe download, LazyEdit processing, and public
platform publication.

## Pipeline Contract

```text
story idea
  -> draft
  -> independent critique
  -> final story
  -> fresh words-card image
  -> visible Xiaoyunque preflight
  -> one paid submission
  -> scoped monitoring and resumable download
  -> full media validation
  -> exact publish selection
  -> LazyEdit processing
  -> AutoPublish terminal platform results
```

Each arrow needs evidence. A downstream completion claim does not repair a
missing upstream proof.

## Configuration

Use local ignored configuration rather than committing machine paths:

```bash
set -a
. "$LAZYSKILLS_LOCAL_CONFIG"
set +a
```

Expected variables include:

```text
LALACHAN_ROOT
LALA_STUDIO_ROOT
LAZYEDIT_ROOT
XYQ_CDP_URL
AUTOPUBLISH_API
```

## Story Gate

For a short episode, require:

- one activity and one problem;
- a visible cause-and-effect chain;
- natural, short dialogue;
- distinct character actions;
- one clear payoff;
- no production notes inside the story.

Run a separate critic pass. The critic quotes exact weak wording and checks
clarity, duration, causality, natural speech, warmth, visual comedy, and
shareability. Only the final rewrite advances to video preparation.

## Words-Card Gate

Keep field names in story metadata when the parser needs them. Never render the
field names on the physical card.

1. Choose one episode-relevant concept.
2. Verify that every language value means that concept and is correctly
   written in its own script.
3. Use the supplied words-card product image as the image-generation reference.
4. Render only the values as four lines:

```text
{{VALUE_1}}
{{VALUE_2}}
{{VALUE_3}}
{{VALUE_4}}
```

5. Do not add language names, field labels, colons, bullets, numbering, or
   explanations.
6. Inspect the generated PNG at original resolution.
7. Compare every character with the requested values and confirm semantic
   equivalence across the lines.
8. Regenerate before paid submission when any line is inaccurate, unreadable,
   mislabeled, missing, or duplicated.

Save the accepted image as `generated-word-card.png` in the current run and
upload it instead of the base card reference.

## Observable Browser Gate

Use the persistent, logged-in Xiaoyunque profile and a visible noVNC desktop.
Do not substitute a temporary profile.

For the lite noVNC client, use fit-to-window scaling:

```text
vnc_lite.html?...&scale=1
```

`resize=remote` is not interpreted by `vnc_lite.html` and can leave the remote
canvas clipped.

Use Studio's visible controller:

```bash
cd "$LALA_STUDIO_ROOT"
scripts/launch_studio_novnc.sh start --project-root "$LALACHAN_ROOT"
scripts/launch_xyq_novnc.sh start
node tools/lala-studio-browser.mjs status
```

## Xiaoyunque Preflight

Verify all of these in one screenshot or equivalent visible evidence:

- intended thread and logged-in profile;
- requested mode;
- cheapest approved model;
- requested duration;
- requested ratio;
- exact prompt;
- every required attachment in success state;
- no unintended Trio attachment;
- identity anchors for all main characters;
- generated words card uploaded as the correct attachment;
- visible credit estimate accepted by the user.

The prompt refers to uploaded assets as `图1`, `图2`, and so on. It never
contains local paths. Describe the words card as an already-made physical prop
whose four lines should remain accurate and unlabeled.

Prepare first when useful:

```bash
node tools/lala-studio-browser.mjs production \
  --operation prepare \
  --message "Prepare the current short video"
```

Submit only after explicit approval:

```bash
node tools/lala-studio-browser.mjs production \
  --operation generate \
  --confirm-paid \
  --wait-seconds 7200
```

Click once. A point decrease, queued state, or running state proves acceptance.

## Download Gate

Use the scoped watcher:

```bash
python "$LALACHAN_ROOT/scripts/xyq_chrome/watch_thread_dom_download.py" \
  --cdp-url "$XYQ_CDP_URL" \
  --page-id PAGE_ID \
  --thread-url THREAD_URL \
  --output-dir RUN_DIR \
  --filename EPISODE.mp4 \
  --expected-duration 15 \
  --copy-to "$LALACHAN_ROOT/Videos"
```

The watcher must:

- inspect only the current result card/preview;
- write and resume a `.part` file;
- honor the server byte count;
- use Range requests after interrupted transfers;
- atomically rename only a complete file;
- reject unrelated or stale media;
- reject duration mismatches;
- decode the complete video and audio streams.

Header duration alone is insufficient. Validate:

```bash
ffmpeg -v error -xerror -i EPISODE.mp4 \
  -map 0:v:0 -map 0:a:0? -f null -

ffprobe -v error -count_frames \
  -show_entries format=duration,size \
  -show_entries stream=codec_type,codec_name,width,height,nb_frames,nb_read_frames \
  -of json EPISODE.mp4

sha256sum EPISODE.mp4
```

Extract sample frames near the start, middle, and end. Missing late frames mean
the transfer is incomplete even when the container advertises the target
duration.

## Publish Preflight

After generation, refresh Studio's story/video inventory. Select the exact
matching filename; never trust a previous selection.

Verify:

- exact MP4;
- exact story context;
- polished ASR plus story correction;
- correct publish category;
- intended platforms;
- portrait blur-fill;
- multilingual subtitles/readings;
- configured top-right logo.

The normal LALACHAN publish shape is:

```bash
cd "$LAZYEDIT_ROOT"
python scripts/lazyedit_publish.py \
  --video "$LALACHAN_ROOT/Videos/EPISODE.mp4" \
  --title "PUBLIC TITLE" \
  --source lalachan \
  --platforms shipinhao,youtube,instagram,douyin \
  --publish-category lalachan \
  --use-current-settings \
  --prompt-file "$LALACHAN_ROOT/references/stories/EPISODE.md" \
  --correct-subtitles \
  --process --publish \
  --burn-subtitles \
  --portrait-blur-fill \
  --portrait-blur-mode lalachan \
  --logo --logo-position top-right \
  --guided-monitor --wait --json
```

The story is correction and metadata evidence, not public copy to paste
verbatim. Let LazyEdit produce normal viewer-facing metadata.

## Processed-Master Gate

Before reporting completion, inspect the processed output:

- portrait dimensions;
- source-aspect foreground remains sharp;
- blurred background fills the frame;
- subtitle reserve is readable;
- subtitles match story and ASR context;
- language readings render correctly;
- logo is at the configured corner;
- full media decode succeeds;
- ZIP contains the intended MP4, cover, metadata, and subtitle artifacts.

## Platform Monitoring

Monitor AutoPublish until terminal status:

```bash
curl -fsS "$AUTOPUBLISH_API/publish/queue" | jq .
```

Platform notes:

- Shipinhao login can require a QR email. Wait for authentication rather than
  restarting all platforms.
- Collection assignment is best-effort; report an unavailable collection.
- YouTube playlist creation and immediate selection can race. Report the
  fallback but preserve a successful publish.
- Instagram should retain Original crop for the prepared portrait master.
- Douyin needs management-page verification after the publish click.

If one platform fails, reuse the same verified ZIP and retry only that platform.
Do not reprocess the video or republish platforms already proven successful.

## Common Failure Table

| Evidence | Response |
| --- | --- |
| Card contains labels | Regenerate an unlabeled card |
| Any card line is inaccurate | Correct values and regenerate before video submission |
| Base card uploaded | Replace it with the verified episode PNG |
| Prompt contains a path | Remove it and refer to uploaded `图N` assets |
| Attachment is still uploading | Wait or repair; do not submit |
| Wrong model or ratio | Correct and recapture preflight |
| Existing generation is queued | Monitor; never click submit again |
| MP4 duration looks right but late frames fail | Resume or re-download and require full decode |
| Wrong video selected for publishing | Refresh inventory and select exact filename |
| noVNC is clipped | Use `scale=1` |
| One platform fails after others succeed | Retry only the missing platform with the same ZIP |

## Completion Report

Report:

- story path;
- generated words-card path;
- noVNC link;
- Xiaoyunque thread;
- mode/model/duration/ratio;
- attachment count;
- number of paid submissions and observed credit change;
- MP4 path, duration, dimensions, codecs, byte count, and hash;
- processed master and ZIP paths when publishing;
- terminal status for every requested platform;
- collection/playlist or other best-effort limitations.

