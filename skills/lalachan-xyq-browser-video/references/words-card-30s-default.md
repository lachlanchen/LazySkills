# Words Card and 30s Workflow

Use this when preparing LALACHAN Xiaoyunque prompts with the eight-image
reference set for an explicitly requested 30-second episode.

## Duration

Target for this workflow: `30秒`. The ordinary LALACHAN default remains `15秒`.

Do not silently compress a story to `15秒` just because the `沉浸式短片` controls
are capped at 15 seconds. Use the 30s-capable Agent/integrated workflow instead.

Use `15秒` for ordinary daily episodes, quick tests, low-credit requests, or
whenever the user explicitly asks for the short-film workflow.

## Words Card Prompt

Use `words-card.jpg` as the visual image-generation reference. Generate a fresh
episode-specific PNG before upload and treat that generated card as a small
physical prop inside the scene:

```text
图1 是已经制作好的实体学习卡，可作为场景边缘、桌面、道具架或实验台上的小道具。
卡片只显示上传图片中的四行正文，不加语言名称、字段标签、冒号、项目符号或编号。
保持每一行文字准确清楚。
它只是场景里的真实道具，不是字幕，也不是画面说明文字。
```

Pick the word from the story theme. Story metadata may use labels for parsing:

```text
English: courage
Japanese: 勇気
Furigana: ゆうき
中文：勇气
```

The generated card face itself shows only `courage`, `勇気`, `ゆうき`, and
`勇气`, one line each. Verify that every line is accurate and expresses the
same concept before upload. The card supports the scene; it does not replace the
story or become overlay text.
