# Shipinhao Source-Scoped Media Transcription

Use this workflow when a WeChat Channels/Finder share must be understood from
its actual audio rather than its card title or comments.

## Order

1. Resolve the exact current chat row and `<finderFeed>` identity.
2. Try the exact allowlisted Tencent media URL with bounded download.
3. If the signed URL expired, open the exact card in native WeChat and leave the
   player visible.
4. Run the repository's `shipinhao_gui_audio_capture.py` with object ID, exact
   title/author, and one or more distinctive OCR identity terms.
5. Require a private `verified-capture.json` whose object ID, metadata, audio
   path, and SHA-256 all match.
6. Run `shipinhao_media_transcribe.py --capture-manifest ...`.
7. Give the timestamped transcript to the same chat's resumed worker agent.
8. Send a natural summary through the guarded same-chat sender and verify mirror
   states `sent`, `done-sent`, and `synced`.

## Capture Command

```bash
python <REPO>/agentic_tools/wechat_gui_agent/scripts/shipinhao_gui_audio_capture.py \
  --object-id '<OBJECT_ID>' \
  --title '<CARD_TITLE>' \
  --author '<AUTHOR>' \
  --identity-term '<DISTINCTIVE_TERM>' \
  --display ':97' \
  --json
```

The helper uses the native `WeChat` window, `WeChatAppEx` PipeWire output,
local OCR, and the shared GUI lock. It does not navigate, post, like, follow, or
invoke Yuanbao. Monitoring is local and consumes no agent/model tokens.

## Non-Negotiable Gates

- Fail when identity is absent before recording.
- Do not reload after binding the audio stream; the node may be replaced.
- Detect source end from visible identity loss, not nominal duration alone.
- Trim auto-advanced feed items before transcription.
- Keep audio, screenshots, URLs, transcripts, and manifests private/ignored.
- Comments remain auxiliary evidence and use a separate comment export path.
- If no exact source evidence exists, answer with an explicit limitation.
