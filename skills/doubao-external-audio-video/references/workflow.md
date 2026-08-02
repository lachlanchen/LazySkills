# Detailed Workflow

## Prepare Contract

- Same visible Chrome profile and noVNC desktop as the requested session.
- Doubao is logged in.
- Video generation mode is visibly active.
- The external audio and every requested visual reference show attachment
  evidence; typed filenames are not evidence.
- Prompt contains no local paths and clearly identifies soundtrack authority.
- Duration/model/cost are visible and accepted before paid submission.

## Fallback

If the current Doubao video mode cannot upload audio, do not abandon the music.
Generate visuals using the same timed story and reference images, then replace
the generated soundtrack:

```bash
ffmpeg -y -i generated.mp4 -i reviewed-song.mp3 \
  -map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -b:a 192k -shortest final.mp4
```

Verify the final duration and both streams with `ffprobe`.

Doubao result cards may show only a poster until clicked. Activate the latest
completed card before searching for the `<video>` source or download action.

## Failure Rules

- Login/CAPTCHA/credit confirmation: report and wait.
- No upload control: open the visible attachment menu and inspect file inputs.
- Realistic face reference rejected by Seedance: retry once in the same
  conversation as text-to-video, without the face attachment. Preserve the
  local image as composition guidance and record the rejection evidence.
- Partial page: foreground it; use visible Ctrl+L then Enter if navigation did
  not commit.
- Generation queued: monitor the same task. Never create a duplicate.
