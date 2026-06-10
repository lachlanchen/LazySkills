# 30s Agent Browser Workflow

Use this when the user asks for a 30-second Xiaoyunque video and the `沉浸式短片` toolbar is fixed at `15秒` or pushes a VIP short-film model.

## General Steps

1. Use the logged-in browser UI, not the Xiaoyunque API unless the user explicitly asks for API.
2. Go to `创作` and stay in `创作 Agent` / integrated-agent mode.
3. Upload reference files directly with `upload-images-verify`; paths are for upload only and must not appear in the prompt.
4. Use a compact prompt whose first sentence includes `30 秒`, with concise image-order labels and only essential restrictions.
5. Submit from the enabled Agent send button.
6. Monitor the new `integrated-agent` thread with `watch_thread_dom_download.py`.
7. If the Agent pauses for confirmation after storyboard/material creation, answer in the same thread with `继续生成视频。`

## Do Not

- Do not force `沉浸式短片` to 30s when its visible duration control remains `15秒`.
- Do not paste local file paths into the prompt.
- Do not add long repeated negative constraints; keep the prompt readable.
