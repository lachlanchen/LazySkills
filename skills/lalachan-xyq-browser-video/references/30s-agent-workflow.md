# 30s Agent Browser Workflow

Use this by default for ordinary LALACHAN Xiaoyunque video requests. The default target is `30秒`. Also use it when the `沉浸式短片` toolbar is fixed at `15秒` or pushes a VIP short-film model.

## General Steps

1. Use the logged-in browser UI, not the Xiaoyunque API unless the user explicitly asks for API.
2. Go to `创作` and stay in `创作 Agent` / integrated-agent mode.
3. Upload reference files directly with `upload-images-verify`; paths are for upload only and must not appear in the prompt.
4. Use a compact prompt whose first sentence includes `30 秒`, with concise image-order labels and only essential restrictions.
   For the words card, use the stable prop phrasing: `图1 是小白屏学习卡风格参考，可作为场景边缘、桌面、道具架或实验台上的小道具，卡片内容是 English: WORD；Japanese: 日本語；Furigana: ふりがな；中文：中文含义。它只是场景里的真实道具，不是字幕。`
5. Submit from the enabled Agent send button.
6. Monitor the new `integrated-agent` thread with `watch_thread_dom_download.py`.
7. If the Agent pauses for confirmation after storyboard/material creation, answer in the same thread with `继续生成视频。`
8. After using the page `下载` fallback, verify the fresh file in `~/Downloads` by modified time, size, `ffprobe`, and SHA256 before copying. Do not reuse a stale `final_video (*.mp4)`.

## Do Not

- Do not force `沉浸式短片` to 30s when its visible duration control remains `15秒`.
- Do not fall back to `15秒` unless the user explicitly asks for 15s, quick test, cheapest/least credits, or accepts the short-film cap.
- Do not paste local file paths into the prompt.
- Do not add long repeated negative constraints; keep the prompt readable.
- Do not copy a downloaded MP4 until it is proven to be from the current run.
