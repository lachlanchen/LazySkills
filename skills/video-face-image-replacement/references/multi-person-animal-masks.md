# Multi-Person Animal Mask Research

Use this reference when one video contains multiple people and each person should keep a different animal mask across the whole video.

## Recommended Stack

- **InsightFace `FaceAnalysis`** for face boxes, landmarks, and recognition embeddings. The `buffalo_l` model pack gives 512-dimensional embeddings that are useful for re-identification.
- **Face-only identity association first**: combine embedding similarity, bounding-box IoU, and center distance. This is usually enough for talking-head or light-motion videos.
- **ByteTrack or DeepSORT only when needed**: add a person-level tracker if faces disappear, people cross, or identity switches appear in sample clips.
- **SAM 2 only for hard compositing**: use it when masks must respect hands, props, occlusions, or full head/body segmentation. For ordinary face-cover overlays, alpha PNGs on tracked boxes are faster.
- **Persistent `identity_map.json`**: store `track_id -> animal/style/asset` and reuse it for full renders, 2x variants, and section splits.

## Identity Tracking

For every detection frame, store:

```json
{
  "frame_index": 123,
  "bbox": [x1, y1, x2, y2],
  "score": 0.91,
  "embedding": "512-d face embedding"
}
```

Track state:

```json
{
  "track_id": 1,
  "animal": "panda",
  "style": "neutral",
  "last_bbox": [x1, y1, x2, y2],
  "smoothed_bbox": [x1, y1, x2, y2],
  "embedding_ema": "512-d vector",
  "first_frame": 0,
  "last_seen_frame": 882,
  "lost_frames": 0,
  "representative_crop": "artifacts/.../track_001.jpg"
}
```

Start with this association cost:

```text
cost = 0.35 * (1 - IoU(track_box, detection_box))
     + 0.55 * (1 - cosine_similarity(track_embedding, detection_embedding))
     + 0.10 * normalized_center_distance
```

Use Hungarian assignment when multiple tracks and detections exist in the same frame. Keep lost tracks alive for `30-90` frames so short occlusions do not create a new animal identity.

## Animal Assignment

Default order:

```text
panda -> red_panda -> horse -> cow -> giraffe
```

If more than five people appear, repeat the animal set with visible variants, for example `panda_blue_scarf` or `red_panda_green_scarf`.

Example map:

```json
{
  "animal_order": ["panda", "red_panda", "horse", "cow", "giraffe"],
  "tracks": {
    "1": {"animal": "panda", "style": "neutral"},
    "2": {"animal": "red_panda", "style": "neutral"},
    "3": {"animal": "horse", "style": "neutral"}
  }
}
```

## Girl/Boy Style

Use user-provided or source-provided labels when available. If no label is available, generate neutral animal masks.

Do not expose automatic gender inference as a public claim. Attribute classifiers can be useful as private style hints, but they can be wrong and have demographic accuracy disparities. Store automatic outputs only as `style_hint` with confidence and require contact-sheet review before final rendering.

Style examples:

```text
girl_soft: softer lighting, rounder silhouette, subtle pastel accessory
boy_bold: stronger contrast, sharper silhouette, simple dark accessory
neutral: clean studio lighting, no gendered accessory
```

## Asset Generation Prompt

```text
Create one high-resolution front-facing {animal} head mask for video compositing.
The head should be centered, symmetrical, directly facing camera, with clean studio lighting,
no body, no text, no watermark, and generous padding around the full head.
Use {style_description}.
Put the animal head on a perfectly flat solid pure green chroma-key background (#00ff00),
with no shadows, gradients, texture, floor plane, reflection, or green in the subject.
```

After generation, use edge-connected background removal. Do not globally key white or light pixels, because panda/cow/horse masks often contain interior white regions.

## Review And Validation

Before the full render:

1. Detect faces on sampled frames.
2. Build tracks and `identity_map.json`.
3. Write a contact sheet with representative crop, `track_id`, animal, style, and asset path.
4. Merge duplicate tracks manually if the same person appears twice.
5. Render a short sample.
6. Spot-check early, middle, and late frames for identity switches and alignment.
7. Render the full output and validate duration/audio with `ffprobe`.

## Sources

- InsightFace FaceAnalysis guide: `https://www.insightface.ai/guides/insightface-1-0-tutorial`
- InsightFace repository: `https://github.com/deepinsight/insightface`
- ByteTrack paper: `https://arxiv.org/abs/2110.06864`
- ByteTrack implementation: `https://github.com/FoundationVision/ByteTrack`
- DeepSORT paper: `https://arxiv.org/abs/1703.07402`
- SAM 2 official page: `https://ai.meta.com/sam2/`
- DeepFace package: `https://pypi.org/project/deepface/`
- FairFace paper: `https://arxiv.org/abs/1908.04913`
- Gender Shades paper: `https://proceedings.mlr.press/v81/buolamwini18a.html`
