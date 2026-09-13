# Shipinhao Source-Scoped Media Transcription

Use this workflow when a WeChat Channels/Finder share must be understood from
its actual audio rather than its card title or comments.

## Order

1. Resolve the exact current chat row and `<finderFeed>` identity.
2. Try the exact allowlisted Tencent media URL with bounded download.
3. If the signed URL expired, use the selected native transport to copy the
   exact card's share link. For Windows use `shipinhao_tiny11_share_link.py`;
   for the preserved Linux fallback use the existing helper's
   `--share-link-only` mode. Do not inspect a different client's login screen.
4. Validate the recovered link's full title and author against the original
   card. OCR of a cropped title is only discovery evidence, not final identity.
5. Run `shipinhao_media_transcribe.py --recovered-share-url ...` with the
   exact source text. Reuse the existing downloader and configured GPU 1 ASR.
6. Require verified original media and timestamped transcript artifacts.
7. Give the timestamped transcript to the same chat's resumed worker agent.
8. Send the original video, readable transcript and one natural summary through
   the guarded same-chat sender. Require actual delivery receipts, not merely
   a successful queue or GUI click.

## Windows Link Recovery

```bash
<VISION_PYTHON> <REPO>/agentic_tools/wechat_gui_agent/scripts/shipinhao_tiny11_share_link.py \
  --chat '<EXACT_CHAT>' \
  --source-text-file '<PRIVATE_TASK_DIR>/exact-source-card.txt' \
  --output-dir '<PRIVATE_TASK_DIR>/windows-native-link'
```

The helper reuses the logged-in native client and shared GUI lock. It uses
Silent Play and Copy Link, never forwarding, liking, following or commenting.
Download and transcription happen after releasing the GUI. Read the LabCanvas
reference `references/windows-wechat-channels-originals-and-send-reconciliation.md`
for source binding, thumbnail crops, composer checks and native video receipts.

The native player can be a separate `WeChatAppEx` descendant process. Preserve
its menu focus only after verifying app-specific executable path, session and
live ancestry; refocusing the parent chat app closes Copy Link without copying.
Do not relax cross-app guards or use a process name alone. If the selected
client itself requests login, stop native recovery and retain unfinished source
tasks. A passing test suite or one recovered card is not proof that every card
was downloaded. Never resend a completed source while repairing another.

## Non-Negotiable Gates

- Never substitute a screen/player/audio recording for an original download.
- Keep one identity and delivery ledger per card, including consecutive cards.
- Preserve the agent's source selection when normalizing a route.
- Reconcile an uncertain send before retrying. Windows can remux MP4 containers;
  verify the native row digest and every audio/video stream's unchanged hash.
- Empty clipboard text is not proof of an empty attachment composer.
- Keep audio, screenshots, URLs, transcripts, and manifests private/ignored.
- Comments remain auxiliary evidence and use a separate comment export path.
- If no exact source evidence exists, answer with an explicit limitation.
