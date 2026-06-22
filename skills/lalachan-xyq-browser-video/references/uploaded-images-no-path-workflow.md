# Uploaded Images, No Local Paths

Use this when preparing LALACHAN Xiaoyunque videos with the current eight-image
reference set. The paths below are upload inputs only. Do not paste them into
the Xiaoyunque prompt.

## Reference Order

| Label | File | Meaning |
| --- | --- | --- |
| 图1 | `words-card.jpg` | words card / 小白屏学习卡 style reference; show a fresh English/Japanese/furigana word each episode |
| 图2 | `LazyingArtRobot.png` | robot `庄子`; keep LazyingArt chest logo |
| 图3 | `display.png` | LightMind AI glasses |
| 图4 | `patchwork-leather-notebook-luxury-clean-v2.png` | handmade patchwork notebook |
| 图5 | `raraxia.jpeg` | individual 啦啦侠 / Rara Xia reference |
| 图6 | `ayachan.png` | individual 阿芽酱 / Aya Chan reference |
| 图7 | `sasakun.jpeg` | individual 飒飒君 / Sasa Kun reference |
| 图8 | `Trio.png` | 啦啦侠, 阿芽酱, 飒飒君 group identity reference |

## Upload

```bash
scripts/xyq_cdp_browser.py upload-images-verify PAGE_ID \
  words-card.jpg \
  LazyingArtRobot.png \
  display.png \
  patchwork-leather-notebook-luxury-clean-v2.png \
  raraxia.jpeg \
  ayachan.png \
  sasakun.jpeg \
  Trio.png \
  --timeout 180 \
  --screenshot outputs/xyq-run/after-upload-eight.png
```

Wait until every upload item is `success`. If one image stalls, remove that chip
and retry. A smaller temporary upload copy is allowed for a stubborn large PNG,
but the prompt must still say `图1`, not the temporary path.

## Prompt Rule

Use wording like:

```text
参考图顺序：图1 是小白屏学习卡风格参考，可作为场景边缘、桌面、道具架或实验台上的小道具，
卡片内容是 English: WORD；Japanese: 日本語；Furigana: ふりがな；中文：中文含义。
它只是场景里的真实道具，不是字幕。图2 是机器人庄子；图3 是 LightMind AI 眼镜；
图4 是拼皮笔记本；图5 是啦啦侠单人参考；图6 是阿芽酱单人参考；
图7 是飒飒君单人参考；图8 是啦啦侠、阿芽酱、飒飒君三人角色参考。请只根据这些已经上传的图片参考，
不要把任何文件名或路径画进视频。
```

Choose a new story-relevant learning word for `图1` every time unless the user
explicitly wants to continue the previous word. The card content must include
English, Japanese, and Japanese furigana.

Two methods are valid:

- Pre-generate a new words-card image first with AgInTi/image generation and
  upload that new card as `图1`.
- Upload the existing words-card as the `图1` style/example reference, then give
  Xiaoyunque the exact English/Japanese/furigana content and let it render the
  new card in-scene.

Use either method, or both, as long as it works. Prefer pre-generation when exact
text accuracy matters.

Reject path leakage before submission:

```bash
rg -n '/home|ProjectsLFS|artifacts|\.png|\.jpg|\.jpeg' references/prompts/PROMPT.md || true
```

## Contract

Submit only after proving:

- target duration is `30秒` by default
- if `沉浸式短片` is visibly capped at `15秒`, switch to a 30s-capable Agent/integrated workflow
- use `15秒` only when the user explicitly asks for 15s, quick test, cheapest/least credits, or accepts the short-film cap
- use a relatively cheap suitable model that supports the requested duration; Mini体验版/vipnew at a visible cheap rate such as `单秒限时低至4积分` is preferred, and Fast/Fast VIP/another Seedance row is acceptable when it is the relatively cheaper suitable option
- `4:3` unless requested otherwise
- all eight images attached successfully
- prompt contains no local paths
- no subtitles or extra generated screen text beyond intentional in-scene props such as the words card, `AgInTi`, or `LightMind`
