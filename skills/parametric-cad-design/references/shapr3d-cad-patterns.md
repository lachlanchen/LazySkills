# Shapr3D And Optical CAD Patterns

Use this reference when a task involves Shapr3D `.shapr` archives, old STEP
exports, exact regeneration, OpenHI/Nature optical holders, C-mount adapters,
sensor/PCB holders, or print-fit thread variants.

## Shapr3D Source Handling

On Linux/Ubuntu, a `.shapr` file should first be treated as an archive:

```bash
python skills/parametric-cad-design/scripts/inspect_shapr_step_sources.py \
  --shapr /path/to/design.shapr \
  --step /path/to/step-folder \
  --markdown
```

The important signs are:

- `workspace` is SQLite: inspect table counts and sketches.
- `HistoryTreeNodes.Properties` type `2` nodes can be decoded as MessagePack
  operation records: display name, operation name, and child node IDs.
- Many `HistoryImportedBodies`: likely imported Parasolid/B-rep, not clean
  editable feature history.
- Few or zero `Shapes`: do not assume a parametric Shapr feature tree is
  recoverable.

If the Shapr archive mostly contains imported bodies, the correct path is:

1. preserve exact STEP/Parasolid B-rep as the baseline;
2. document body labels, bounding box, face/surface evidence, and source path;
3. make sibling parametric variants for fit changes;
4. do not overwrite exact regeneration outputs.

## Reading Edit History As Design Knowledge

Shapr operation history is useful even when full feature parameters are not
available. Use it to infer the designer's workflow:

| Signal | Meaning | Better future CAD practice |
| --- | --- | --- |
| Many `MaterializeImportedBodies` | vendor/reference components or flattened assemblies | Keep references locked and build clean generated holders around them. |
| Many `MaterializeSketchPlane` + `Extrude` | sketch-first native design | Recreate with named sketches/profiles and explicit dimensions. |
| Many `Revolve` | cylindrical/optical/tube design | Use section sketch + revolve; keep axis named. |
| Many `OffsetFace` | physical fit tuning, wall-thickness adjustment, or direct-model clearance edits | Convert offsets to named parameters such as `pcb_clearance_xy`, `socket_relief_extra`, `thread_pilot_diameter`. |
| Many `Transform`/`Align` | assembly placement matters | Preserve part coordinate frames and placement transforms; do not bake everything into one originless solid. |
| Many `Boolean`/`Split` | cutters and construction bodies were important | Export cutter bodies separately and document boolean recipes. |
| Many `Chamfer`/`Fillet` | edge handling for insertion, comfort, or printability | Name chamfer/fillet sizes and keep them late in the model. |

Treat high `OffsetFace` count as a maintainability warning. It is good evidence
of successful physical iteration, but a fragile edit chain. Once the fit is
known, rebuild critical regions with parameters.

## Exact Regeneration Versus New Design

Exact regeneration means preserving the existing body:

- import STEP/Parasolid;
- export a new STEP/STL/render;
- verify solid count, bbox, named bodies, cylindrical/conical/B-spline face
  evidence, and thread/chamfer locations;
- avoid rebuilding unless the original B-rep is broken.

New design means using the old part as reference:

- create named parameters;
- choose one datum;
- rebuild clean solids;
- export decomposed bodies so Shapr3D and FreeCAD can edit them.

Do not mix these two modes. A print-fit change should normally be a sibling
variant based on the exact baseline, not a silent edit to the baseline.

## OpenHI/Nature Thread Families

Keep these systems separate:

- Standard C-mount: `1"-32 UN`, nominal major diameter `25.4 mm`, pitch
  `0.79375 mm`.
- Local rounded printed C-mount-style thread: often modeled as `0.8 mm` pitch.
- OpenHI larger lens/BS/top family: near 30 mm, with labels like
  `Thread lens 29.6`, `Thread top`, `Thread BS`, `Outer thread`.

For printed C-mount female sockets, `25.4 mm` should usually be the thread
cutter/groove maximum, not the smooth pilot. A good first experiment is:

- pilot/root: `25.0 mm`;
- cutter max/nominal: `25.4 mm`;
- pitch: `0.79375 mm` or local `0.8 mm`;
- extra runout: about half a pitch, clipped back to final end faces.

For the OpenHI 30 mm receiver print-fit fix:

- old female pilot/start: around `30.2 mm`;
- corrected pilot/start: `30.0 mm`;
- groove/cutter maximum: around `30.4 mm`;
- keep the lens seat and adjust the transition chamfer to land cleanly on the
  new pilot.

## Thread Runout

If a helical thread starts exactly on an end face, the end tooth can be missing
or leave a smooth section. Use construction runout:

- Female thread by subtraction: extend the cutter about half a pitch past the
  intended start/end, then subtract it from the socket.
- Male thread: generate with the same extra half pitch, then trim the final
  solid at the true end faces.
- Do not change tooth height, pitch, or base width when adding runout.

If old threaded B-rep faces produce shell fragments after boolean edits, trim
away the receiver at a stable datum and rebuild the receiver cleanly.

## Alignment And Datum Rules

- Pick one optical axis and drive C-mount, lens seat, sensor active center, PCB
  pocket, and render proxies from it.
- Add pocket clearance symmetrically unless the datasheet gives an intentional
  offset.
- Check whether "not centered" is actually a sensor offset from the board edge.
- Keep component-side, socket-side, sensor-side, long-edge, and short-edge
  directions named in the manifest.

## PCB And Sensor Holder Rules

Use datasheet or board measurements as source of truth:

- board outline;
- mounting hole diameter and centers;
- active sensor center offset;
- connector/socket envelope;
- wire exit direction;
- protrusions such as LEDs, solder joints, pin headers, and DuPont plugs;
- PCB thickness and adhesive thickness if recessed.

The socket relief height should be measured from the PCB surface, not from the
bottom of the holder when the PCB sits in a pocket.

For optical sensor holders, prefer direct clean layouts:

- C-mount socket directly adjacent to sensor plate if no bridge is needed;
- separate solids for C-mount socket, plate/tray, board proxy, sensor proxy,
  thread cutter, and assembly;
- no filler block or decorative saddle unless it solves a real print/support
  problem.

## Artifact Contract

For each serious CAD design, produce:

- parametric source script;
- `README.md` with source measurements, dimensions, and fit notes;
- assembly STEP;
- separate body STEP files;
- printable STL files;
- full-view PNG render;
- optional exploded/detail PNG;
- optional DXF/SVG/PDF sketches for profiles and hole patterns.

Validation should report importability, solid count, bounding box, mesh
watertight/component count, and render path.
