# Full-Song MV vs Chorus / Climax MV

This reference helps decide how to turn a reviewed Musia song into a LALACHAN/Xiaoyunque MV.

## Full-Song MV

Use a full-song MV when the song itself has a narrative or emotional arc. The video should feel like a complete short film set to music.

Recommended duration:

- 45s to 90s for generated character MVs.
- Longer only if the video tool and credit budget can handle it.

Best structure:

| Song Section | Visual Job |
| --- | --- |
| Intro | Establish mood, place, main character, and first visual motif. |
| Verse | Show normal world, friendship, travel, or a small problem. |
| Pre-chorus | Raise tension or reveal danger. |
| Chorus | Biggest action, dance, fight, transformation, or emotional release. |
| Bridge | Change scale, show memory/dream/quiet doubt, or reveal a hidden truth. |
| Final chorus/outro | Resolve conflict and leave one clean final image. |

Prompt pattern:

```text
请根据上传的歌曲音频生成完整音乐MV。画面跟随歌曲段落变化：前奏安静，主歌展开故事，副歌进入最大动作，结尾温暖收束。可以有少量环境声和短台词，但不要压过音乐。不要字幕，不要歌词字幕，不要文件名、路径、说明文字。
```

Full-song dialogue should be sparse. A few memorable lines are better than continuous speech. If vocals are present, put dialogue in transitions or instrumental gaps.

## Chorus / Climax MV

Use a chorus or climax MV when the goal is a short platform cut, fast test, low credits, or a high-energy promo.

Recommended duration:

- 10s, 15s, 20s, or 30s.

Best structure:

| Time | Visual Job |
| --- | --- |
| 0-2s | Start with the strongest image immediately. |
| 2-6s | Bring the characters into motion. |
| 6-12s | Hit the chorus action: charge, dance, transformation, fight, or joke. |
| Final seconds | Clean payoff, loop, pose, or emotional smile. |

Prompt pattern:

```text
请只使用歌曲副歌/高潮部分生成短MV。故事只保留一个核心动作：角色在音乐最高点一起冲刺/跳舞/变身/战斗。镜头跟节拍走，不要复杂剧情，不要长台词，不要字幕。
```

The chorus cut should not try to summarize the whole full MV. It should be a strong hook.

## Choosing Between Them

Choose full-song MV when:

- user says full length, total music, whole song, complete MV;
- the song is already selected and reviewed;
- the user wants story, hope, journey, battle, or emotional resolution;
- the character arc matters.

Choose chorus/climax MV when:

- user says 副歌, 高潮部分, short cut, hook, trailer, preview;
- credits are limited;
- the full song is not ready;
- the visual concept is one strong moment.

## Audio Handling

Try to upload the song as a reference if the video tool supports audio. If the output audio is changed, distorted, replaced, or too quiet, keep the generated visuals and mux the Musia master audio back in.

Verification:

```bash
ffprobe -v error -show_entries format=duration:stream=codec_type,codec_name,width,height \
  -of default=noprint_wrappers=1 OUTPUT.mp4
```

If visual duration is slightly longer than the song, use `-shortest`. If the video is shorter than the song, regenerate or trim the song cut to match the video.

## Handoff Files To Preserve

A good MV handoff folder contains:

- `README.md`: what this MV is and how to use the package.
- `STORY.md`: story, character direction, and dialogue.
- `SEGMENTS.json`: timestamped sections.
- `XYQ_PROMPT_FULL_MV.md` or `XYQ_PROMPT_HOOK_MV.md`: paste-ready prompt without local paths.
- `ASSET_LIST.md`: upload order and labels.
- `SOUND_MIX_NOTES.md`: music, SFX, dialogue, mux policy.
- `HANDOFF.json`: machine-readable local paths for the operator.

Keep local paths in the handoff JSON or local reference docs. Do not paste paths into the Xiaoyunque prompt.

## Common Failure Modes

- **The video tool ignores the song**: prompt more explicitly that music drives timing; if audio is changed, mux locally.
- **Dialogue covers vocals**: reduce dialogue to one or two short lines.
- **Story becomes confusing**: reduce to one cause-effect chain.
- **Long MV costs too much**: make a chorus cut first.
- **Too many uploaded assets**: remove optional props one at a time, but keep character identity references.
- **Metadata becomes a script dump**: use a short viewer-facing metadata brief in LazyEdit.

