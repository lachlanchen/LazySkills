---
name: video-face-image-replacement
description: Use when replacing or covering faces in a video with one supplied image asset, such as a panda head, avatar, logo, or generated mask, using accurate face detection, tracking, background removal, alpha compositing, and ffmpeg audio-preserving output.
triggers:
  - replace face in video
  - cover face with image
  - panda face video
  - face overlay video
  - face mask compositing
  - swap face with avatar
  - remove image background for overlay
  - InsightFace SCRFD face detection
---

# Video Face Image Replacement

Use this skill when a video face should be fully covered or replaced with a supplied image asset. This is the right workflow for non-human masks such as panda, cat, robot, or avatar heads. Human identity swap models are a different workflow and should only be used with consent.

## Core Rules

- Use one source image when the user asks for one generated/reused asset. Do not call image generation again unless explicitly requested.
- Prefer image-overlay replacement for non-human faces. Human face-swap models such as `inswapper_128`, Roop, or FaceFusion assume human-to-human identity transfer and are usually wrong for a panda/avatar mask.
- Preserve the original video and audio. Write a new output file; never overwrite the source.
- Remove green, white, or other simple generated backgrounds locally and composite with alpha.
- Use accurate face detection first, then tracking or detection reuse for speed. Validate with sample frames before processing the full video.
- For private videos, keep raw source media uncommitted and publish only intentional derived clips.

## Detection Choice

Use the best available detector in this order:

- **InsightFace/SCRFD**: strong default for accurate face boxes and landmarks in local Python pipelines.
- **RetinaFace**: accurate alternative when already installed or when landmark quality matters.
- **MediaPipe Face Detector/BlazeFace**: fast, lightweight, good for real-time or mobile-like workflows.
- **OpenCV Haar cascades**: emergency fallback only; fast but less reliable.

For full replacement, enlarge the detected face box enough to cover hairline, ears, chin, and motion jitter. Start with `scale=1.8-2.2` around the face box and tune from sample frames.

## Workflow

1. Copy or reference the video:

```bash
mkdir -p video artifacts/face_replace/{assets,frames,output}
cp -n "/path/to/source.mp4" "video/source.mp4"
ffprobe -v error -show_entries format=duration -show_entries stream=codec_type,width,height,r_frame_rate -of json "video/source.mp4"
```

2. Prepare the replacement image:

- If generated, request a centered mask on a flat chroma-key background.
- If supplied, inspect it first.
- Remove a flat green or white background locally into `replacement_alpha.png`.

3. Extract representative frames and run detection:

```bash
ffmpeg -y -ss 00:00:03 -i video/source.mp4 -frames:v 1 artifacts/face_replace/frames/frame_0003.jpg
ffmpeg -y -ss 00:02:00 -i video/source.mp4 -frames:v 1 artifacts/face_replace/frames/frame_0120.jpg
```

Use InsightFace/SCRFD or another available detector to confirm face count, box coordinates, and confidence on these frames.

4. Render a short sample before the full run:

```bash
python face_overlay.py process \
  --input video/source.mp4 \
  --replacement artifacts/face_replace/assets/replacement_alpha.png \
  --output artifacts/face_replace/output/sample.mp4 \
  --det-size 320 \
  --detect-every 5 \
  --scale 2.0 \
  --limit-frames 150
```

5. Inspect sample frames:

```bash
ffmpeg -y -ss 00:00:03 -i artifacts/face_replace/output/sample.mp4 -frames:v 1 artifacts/face_replace/output/sample_check.jpg
```

Check that the original face is fully covered, the overlay is not too small, and it does not drift off the head.

6. Render the full output:

```bash
python face_overlay.py process \
  --input video/source.mp4 \
  --replacement artifacts/face_replace/assets/replacement_alpha.png \
  --output artifacts/face_replace/output/source_replaced.mp4 \
  --det-size 320 \
  --detect-every 5 \
  --scale 2.0
```

Mux original audio back with `ffmpeg` if the processing script does not preserve it.

## Practical Notes

- For a static talking-head video, detecting every 5-15 frames and reusing the most recent box is usually accurate and much faster than per-frame detection.
- For fast head movement, use a smaller `detect_every`, optical-flow tracking, or detector correction on every frame.
- If there are multiple people, either process all faces or choose the target by area, position, or a reference face embedding.
- If the asset has hair/fur, chroma-key removal may leave fringing. Use despill and a slight alpha feather.
- If the overlay must match head angle, generate or prepare a small view set instead of one image; one asset cannot fully match large yaw/pitch changes.

## Validation Checklist

- Source video copied or referenced without overwriting.
- Replacement asset has alpha and no visible keyed background.
- Detector finds the intended face on sample frames.
- Sample clip shows complete face coverage.
- Full output preserves audio and expected duration.
- Spot checks from early, middle, and late sections show the overlay remains aligned.
- Raw media and private generation metadata are not committed unless explicitly requested.
