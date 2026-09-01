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

For the exact six-file OpenHI collection, direct STEP measurement gives a
`0.4 mm` radial tooth height, not `0.2 mm`. Therefore a pivot changes to its
crest/groove by `0.8 mm` in diameter. The coordinated revision is:

- old `29.6` male / `30.2` female pivots -> `29.8` / `30.0`;
- old `29.8` male / `30.2` female pivots -> `30.0` / `30.0`;
- resulting first-family crest/groove: `30.6` / `30.8`;
- resulting second-family crest/groove: `30.8` / `30.8`.

Keep the `25.5 mm` lens seats and adjust the transition chamfers only where
the tighter `30.0 mm` female pilot must meet the preserved seat.

### Earlier OpenHI 30 mm Printed Coupon Pair

For an earlier independently designed printed coupon pair, do not call every
construction diameter the "nominal" or "pivot" diameter. Record four values:

- male root cylinder: `29.8 mm`;
- male crest: `30.2 mm`;
- female land/pilot bore: `30.0 mm`;
- female groove/cutter maximum: `30.4 mm`.

With that coupon's `0.8 mm` pitch, `0.2 mm` radial tooth height, and `0.8 mm` tooth base,
this leaves `0.2 mm` diametral clearance at both root/land and crest/groove.
Remember that a `0.2 mm` radial tooth changes diameter by `0.4 mm`. This
coupon profile is not the same as the exact six-file OpenHI source profile,
whose radial tooth height is `0.4 mm`.

When one adapter must cover a larger reference chamfer and then screw into a
smaller holder, keep the adapter as one continuous body with two axial regions.
The lower cup OD must be sized by the largest reference shoulder; the upper
thread root must be sized by the mating thread. For the OpenHI C-branch sample
holder, this means a `42 mm` OD cup around a `40.2 -> 25.5 mm` smooth cavity,
followed by the `29.8/30.2 mm` male threaded extension. Do not shrink the whole
cup to `29.8 mm`; it would no longer cover the roughly `40 mm` chamfer.

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

## Split Male Thread Solids

The flattened OpenHI STEP exports can store one male interface as two solids:

- a low-volume swept helical tooth body;
- a root cylinder that belongs to the adjacent main body.

Inspect solid labels, volumes, cylinders, and B-spline envelopes before
editing. To enlarge the pivot, rebuild the tooth body at the new root/crest and
union a thin annular sleeve onto the imported root cylinder. Do not replace the
tooth body with a complete threaded cylinder; that duplicates the root volume,
changes assembly semantics, and can still pass a shallow validity check. Verify
the final root and crest independently after STEP round-trip.

## Avoiding Slow Shapr3D STEP Repair

Shapr3D can import an OCCT-valid STEP slowly or repair it badly when the file
contains fragile topology. Symptoms include:

- long "repairing" on import;
- helical threads disappearing after import;
- transparent or broken-looking faces;
- thread/pocket regions importing as partial shells.

The OpenHI A+C+BS receiver fix showed the reliable pattern:

1. Keep the stable original STEP body as the outer body and preserve complex
   local geometry such as the BS slope/slot.
2. Identify the fragile region by face evidence. Helical thread surfaces often
   appear as B-spline faces.
3. Do not keep adding broad fill-and-recut booleans around the fragile area.
   They can leave internal slivers that Shapr repairs poorly.
4. Add a clean analytic sleeve/socket only inside the mating region.
5. Recut the smooth pilot/root bore with cylinders/cones/planes.
6. For a Shapr-target "threaded" preview, use bounded ring-groove cuts instead
   of helical B-spline threads.
7. Also export a smooth editable STEP with no thread preview.
8. Re-import the exported STEP and verify one solid, expected bbox, B-rep
   validity, and acceptable B-spline face count.

For the OpenHI A+C+BS case, the final Shapr-friendly files preserved the
original `40 x 40 x 84.9 mm` envelope and removed all B-spline thread faces
from the Shapr-target exports. The root-level handoff file was named
`USE_THIS_openhi_a_c_bs_receivers_30p0_30p4_print_fit.step`.

Use this pattern whenever the user reports that Shapr import is slow, Shapr
repairs for a long time, threads vanish, or imported faces become transparent.
If the user needs real editable threads, send the smooth STEP and add native
Shapr threads there, or treat the print as a physically tapped part.

## OpenHI 4f Lens And Receiver Datums

Do not treat a curved lens's annular support seat as its optical-axis surface
vertex. For every A/B/C branch, record four separate positions:

- inward optical-axis surface vertex;
- inward annular support contact at the selected support radius;
- outward annular support contact at the same radius;
- external flange or tube-end plane.

Place the inward optical vertex at the requested focal datum. Derive the
holder seat from the inward surface sag. Derive the matching cap contact from
the support-to-support lens envelope plus the named tightening clearance. A
fully inserted pair must retain the finite lens while preserving full thread
engagement and zero lens/part interference. Lens thickness belongs inside this
cavity; do not add half or all of it again to the `2f` or `4f` distance.

The original OpenHI A input is another independent datum. Its working lower
receiver is about `12.474 mm` deep with a `25.0 mm` pilot and `25.8 mm` helical
groove envelope, but the mating flange seats at the A outer face. Therefore
the insertion depth lies inside the A arm and is not a second focal-distance
allowance. When adapting A:

1. isolate the source lower receiver solid;
2. subtract it from a bounded cylinder to recover the exact internal void;
3. translate that void to the new A flange plane;
4. cut it from the regenerated A body;
5. continue from its 25.0 mm top pilot through a manufacturable transition to
   the lens-specific aperture;
6. compare expected and generated voids in both directions inside the same
   bounded receiver domain;
7. verify nonzero helical relief beyond a smooth pilot and adequate remaining
   wall where the receiver passes inside another thread root.

For visual verification, export a half section through the optical axis and
look from the removed half. A camera on the retained side only shows the
outside thread and can falsely suggest the internal receiver is missing.

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

Do not use the visible connector housing as a substitute for PCB-side pin
geometry. Through-hole solder tails can protrude into the seating surface even
when the housing clears the holder. Model their row on the PCB datum. When the
clearance diameter exceeds the pitch, union the holes with a bridge cutter to
make one continuous slot and eliminate fragile webs between pins.

When an existing optical datum is already correct, a safer PCB recess can be
made by keeping the original seating plate and adding the requested recess
depth as a raised rim outside the PCB footprint. For a 1.5 mm PCB and 2.0 mm
rim, the installed board finishes 0.5 mm below the rim while the sensor,
thread, pilots, and pin-tail relief remain on their validated planes.

For optical sensor holders, prefer direct clean layouts:

- C-mount socket directly adjacent to sensor plate if no bridge is needed;
- separate solids for C-mount socket, plate/tray, board proxy, sensor proxy,
  thread cutter, and assembly;
- no filler block or decorative saddle unless it solves a real print/support
  problem.

## Adapting A Proven Holder To A New Optical Mount

When the sample-facing or PCB-facing holder geometry is already physically
accepted, do not redraw it while changing the mounting interface. Import or
call the accepted parametric feature functions, omit only the obsolete mount
operation, and place the replacement mount in a separate registered body.
Use a shallow named spigot/pocket pair so uncertain fit changes remain local.
For a measured smooth receiver around a threaded reference, record both the
plain-body diameter and thread-crest envelope, then provide a small fit coupon
when the selected ID is tight. Clip large reference assemblies to the exact
mating region for fit renders; never include reference hardware in print files.
Compare bbox, volume, solid count, and feature probes against the accepted
holder before declaring unaffected geometry unchanged.

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

Separate edit and print packaging. An imported Shapr/OpenHI assembly can have
valid bodies hundreds of millimetres above the global origin and can preserve
thread teeth as separate touching solids. Keep that exact placement in the
editable STEP evidence, but create a distinct `PRINT_THIS` handoff. The print
STEP/STL/3MF must use a deliberate print orientation, sit at `Z=0`, and produce
a nonempty first layer. If thread teeth and roots are separate overlapping
solids, union them only in the print copy so the slicer receives one watertight
physical solid. A single intended print should be one 3MF model object and one
build item; otherwise Qidi/Orca-family slicers can ask whether to split the
model and then report an empty initial layer. Verify these properties from the
serialized 3MF and tessellated triangles, not only from an in-memory CAD
preview. Keep the exact editable multi-solid STEP unchanged.

When the user says "Nutstore sync", use:

```text
/home/lachlan/Nutstore Files/Projects/LabCanvas
```

Copy the final `*_assembly.step` there after generation, preserving the
descriptive filename. Keep the complete editable source and full artifact set in
the design folder; the Nutstore copy is a handoff copy for Shapr3D/LabCanvas.
When a folder contains many STEP files, also create and sync one root-level
`USE_THIS_<design>.step` so the user has an unambiguous import target.

Validation should report importability, solid count, bounding box, mesh
watertight/component count, render path, and Nutstore sync path when used.
