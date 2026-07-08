---
name: parametric-cad-design
description: Use when designing, revising, validating, documenting, or rendering mechanical CAD parts with OpenSCAD, CadQuery/build123d/OCP, FreeCAD, Blender, STEP/STL/DXF/SVG/PDF exports, print-fit compensation, versioned artifacts, or old STEP reference measurements.
---

# Parametric CAD Design

Use this skill for agent-assisted mechanical design where the deliverable should remain editable and reproducible, not just a one-off mesh.

## Core Workflow

1. Inspect existing CAD and references first. Prefer `rg --files`, `find`, STEP labels, and measured bounding boxes over visual guesses.
2. Keep dimensions in named parameters in the source model. Do not globally scale a whole part to tune fit.
3. Preserve prior generated outputs in versioned artifact folders, for example `artifacts/v1_.../` and `artifacts/v2_.../`.
4. Generate printable STL from the parametric source, lightweight/envelope STEP for CAD review, and threaded/detailed STEP when the thread geometry matters.
5. Render a full-view PNG and an exploded/detail PNG with Blender when the user needs visual inspection.
6. Validate with mesh and STEP imports before committing.

## Geometry Discipline

- Pick one datum and keep every related feature aligned to it. For optical parts, the optical axis should drive C-mount bores, sensor packages, board pockets, and renders.
- Keep mating bodies editable. Export separate STEP/STL bodies for sockets, plates, inserts, thread cutters, boards, and fixtures when the user may edit them in Shapr3D or FreeCAD.
- Avoid accidental connector geometry. If the user asks for direct contact, remove bridge blocks and middle cylinders; do not replace one unwanted bridge with another.
- Bound threads inside their parent length. A thread cutter for a socket from `x=0` to `x=H` should start after a small lead-in and end before `H`; then clip/intersect the swept thread so no tooth overflows beyond either end.
- Document the contact plane between independent bodies, for example `socket x=0..12`, `plate x=12..19`.
- Use clearance holes and pockets for real protrusions such as pin headers, solder joints, cables, screws, and printed-fit errors. Keep those clearances named and visible in the manifest.
- Prefer simple, clean solids over decorative or overly coupled boolean shapes. If Shapr3D reports invalid geometry when editing, split the part into independent adjacent bodies and bounded cutters.

## Print-Fit Measurement

When adapting old 3D-printed parts:

- Measure old STEP solids by named BRep labels such as `Thread camera 24.4`.
- Record male and female values separately. A male part that inserts into another part is usually kept smaller; the receiving hole/socket/pocket is enlarged.
- Maintain a table for all mating fits: threaded parts, slip-fit pockets, square modules, pins, holes, and optical holders.
- Use a test coupon for uncertain threads before printing large parts.
- Do not confuse standard C-mount with the user's larger OpenHI lens/BS/top thread family. C-mount is `1"-32 UN`, nominal major diameter `25.4 mm`, pitch `0.79375 mm`. The OpenHI lens/BS/top family is near 30 mm and should not be converted to 25.4 mm unless the user explicitly asks for a new C-mount adapter.
- For the OpenHI Lens C holder receiver, the corrected print-fit variant changes the positive-X female from the old `30.2 mm` start/root to `30.0 mm` start/root and cuts a `30.4 mm` groove envelope. Preserve the 25.5 mm lens seat and adjust the 45 degree transition chamfer from `25.5 -> 30.0 mm` over `2.25 mm`.
- `Nature.shapr` and the flattened `cad/extracted/OpenHI_STEP/` exports can describe the same bodies. On Ubuntu, exact regeneration should usually preserve the exported STEP B-rep, because the `.shapr` often stores imported Parasolid bodies rather than editable feature history.

For helical threads made from a swept triangle, document:

- root diameter and crest diameter;
- pitch or gap;
- tooth height;
- tooth base width;
- thread hand and viewed-from direction;
- thread length and unthreaded lead-in length.

## Useful Commands

Generate OpenSCAD STLs:

```bash
openscad -D 'part="tube"' -o artifacts/v2/tube.stl model.scad
openscad -D 'part="holder"' -o artifacts/v2/holder.stl model.scad
```

Generate STEP/drawings with a repo-local CAD Python kernel:

```bash
cad/.conda/cad-python/bin/python path/to/generate_support_artifacts.py
```

Render with Blender:

```bash
blender --background --python path/to/blender_render.py
```

Validate meshes:

```bash
cad/.conda/cad-python/bin/python - <<'PY'
import trimesh
mesh = trimesh.load("artifacts/v2/assembly.stl", force="mesh")
print(mesh.is_watertight, len(mesh.split(only_watertight=False)), mesh.bounds[1] - mesh.bounds[0])
PY
```

Validate STEP bounds:

```bash
cad/.conda/cad-python/bin/python - <<'PY'
import cadquery as cq
shape = cq.importers.importStep("artifacts/v2/assembly.step")
bb = shape.val().BoundingBox()
print(bb.xlen, bb.ylen, bb.zlen)
PY
```

## Completion Report

Report the source model path, current artifact folder, STL/STEP/DXF/SVG/PDF/PNG outputs, measured bounds, watertight/component checks, render path, commit hash, push status, and any remaining physical fit checks.
