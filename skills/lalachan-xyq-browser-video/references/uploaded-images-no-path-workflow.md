# Uploaded Images, No Local Paths

Use this when preparing LALACHAN Xiaoyunque videos with the current seven-image
reference set. The paths below are upload inputs only. Do not paste them into
the Xiaoyunque prompt.

## Reference Order

| Label | File | Meaning |
| --- | --- | --- |
| 图1 | `artifacts/images/2026-06-07T02-10-31-891Z/image.png` | words card / 小白屏学习卡; show a fresh word each episode |
| 图2 | `LazyingArtRobot.png` | robot `庄子`; keep LazyingArt chest logo |
| 图3 | `display.png` | LightMind AI glasses |
| 图4 | `patchwork-leather-notebook-luxury-clean-v2.png` | handmade patchwork notebook |
| 图5 | `R1.jpg.jpeg` | 啦啦侠 clothing reference |
| 图6 | `R3.jpg.jpeg` | 飒飒君 clothing reference |
| 图7 | `Trio.png` | 啦啦侠, 阿芽酱, 飒飒君 identity reference |

## Upload

```bash
scripts/xyq_cdp_browser.py upload-images-verify PAGE_ID \
  artifacts/images/2026-06-07T02-10-31-891Z/image.png \
  LazyingArtRobot.png \
  display.png \
  patchwork-leather-notebook-luxury-clean-v2.png \
  R1.jpg.jpeg \
  R3.jpg.jpeg \
  Trio.png \
  --timeout 180 \
  --screenshot outputs/xyq-run/after-upload-seven.png
```

Wait until every upload item is `success`. If one image stalls, remove that chip
and retry. A smaller temporary upload copy is allowed for a stubborn large PNG,
but the prompt must still say `图1`, not the temporary path.

## Prompt Rule

Use wording like:

```text
参考图顺序：图1 是小白屏学习卡，每集显示新的主题词；图2 是机器人庄子；图3 是 LightMind AI 眼镜；
图4 是拼皮笔记本；图5 是啦啦侠服装参考；图6 是飒飒君服装参考；
图7 是啦啦侠、阿芽酱、飒飒君三人角色参考。请只根据这些已经上传的图片参考，
不要把任何文件名或路径画进视频。
```

Choose a new story-relevant English/Japanese learning word for `图1` every time
unless the user explicitly wants to continue the previous word.

Reject path leakage before submission:

```bash
rg -n '/home|ProjectsLFS|artifacts|\.png|\.jpg|\.jpeg' references/prompts/PROMPT.md || true
```

## Contract

Submit only after proving:

- `沉浸式短片`
- normal/non-VIP `Seedance 2.0 Fast` unless requested otherwise
- `15秒`
- `4:3` unless requested otherwise
- all seven images attached successfully
- prompt contains no local paths
- no subtitles or generated screen text requested
