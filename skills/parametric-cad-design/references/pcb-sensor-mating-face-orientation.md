# PCB and Sensor Mating-Face Orientation

Use this reference when a holder is derived from a PCB sketch, component-side
photo, solder-side photo, rear view, front elevation, vendor image, or physical
measurement. It prevents correct dimensions from being placed on the wrong
side of an asymmetric holder.

## Establish the View Contract

Before modeling, define:

- source face: component, solder, front, rear, or another named face;
- mating face: the surface presented to the holder;
- optical/depth axis;
- PCB long and short axes;
- positive direction for each axis;
- datum, usually the active sensor or optical center;
- which dimensions are measured and which are visual estimates.

Do not use unqualified left/right/top/bottom labels in parameters or drawings.
Use names such as `component_view_pin_row_short_axis_mm` and
`holder_view_pin_relief_short_axis_mm`.

## Map the Face, Not the Whole Holder

A component face pressed against a holder is viewed from the opposite side.
Depending on the chosen axes, one in-plane coordinate may change sign. Write the
mapping before editing. For example:

```text
long_holder = long_source
short_holder = -short_source
```

This does not imply that the complete holder should rotate. If the C-mount,
optical axis, plate, thread, and depth stack are already correct, preserve them
and transform only the PCB-face features: pocket, package opening, mounting
holes, pin-tail relief, wire exit, or LED clearance.

If a full rigid transform is genuinely required, write its matrix or axis-angle
definition and transform every dependent feature together. Never mix a partial
visual mirror with an unexplained whole-body rotation.

## Evidence Hierarchy

Use evidence in this order:

1. measured dimensions and explicit user corrections;
2. official mechanical drawings or verified PCB files;
3. accepted prior CAD and successful physical prints;
4. calibrated orthographic photos;
5. perspective photos for orientation only.

Photos can establish which edge contains a socket or whether the sensor is on
the component side. They usually cannot justify adding detailed connector,
daughterboard, bracket, or notch geometry. Keep such details as separate proxies
unless their clearance is requested and measured.

## Narrow-Change Discipline

When the user says the baseline is good:

1. freeze the accepted run;
2. list parameters allowed to change;
3. calculate each delta from the baseline;
4. keep every unaffected datum as a test assertion;
5. rebuild from the accepted source, not from a rejected intermediate run.

Words such as "slight", "almost correct", and "small adjustment" are important
constraints. A change from `0.0` to `-0.4 mm` is plausibly slight; a move to
`+7.6 mm` is not. Stop and re-evaluate when a verbal interpretation produces a
large delta.

## PCB Pocket and Protrusion Rules

- Keep the active sensor center, not the PCB center, on the optical axis.
- Measure mounting holes and protrusions from the same sensor datum.
- Model PCB-side solder tails separately from the visible connector housing.
- If adjacent tail clearances overlap, unite them into a continuous slot so no
  fragile webs remain.
- Measure socket and wire relief from the PCB seating plane.
- To sink a PCB without moving an accepted optical depth, keep the structural
  plate and add a raised perimeter outside the pocket. For example, a 2 mm rim
  around a 1.5 mm PCB leaves its outer face 0.5 mm below the rim.
- Keep board, package, pins, and housing proxies separate from the printable
  holder unless they are intentional parts of the print.

## C12880MA Case Study

The C12880MA holder demonstrated the method:

- source component view: sensor above, socket/pin row below;
- source PCB center on short axis: `-1.1 mm`;
- source pin-row short-axis coordinate: `-9.3 mm`;
- holder mating view: PCB center `+1.1 mm`, relief `+9.3 mm`;
- long-axis pin-row center stayed near the accepted baseline and changed only
  from `0.0` to `-0.4 mm`;
- C-mount, plate, optical axis, thread, sensor depth, and PCB seating plane did
  not move;
- visible connector/daughterboard details stayed out of printable geometry;
- run 3 and corrected run 5 remained one valid solid with the same
  `42 x 42 x 23 mm` envelope and only about `0.004 mm^3` numerical volume
  difference.

The failed approaches were treating a rear view as the source view, rotating
the whole holder, inventing photo-derived structure, converting ambiguous edge
margins into a large pin-row move, and losing the accepted PCB sink while
resetting geometry.

## Required Visuals

For asymmetric modules, generate at least:

- source-view or holder-mating-view alignment drawing with axis arrows;
- depth-section drawing showing C-mount, package, seating plane, PCB, pocket,
  rim, and connector relief;
- direct-print render;
- assembly render using separate board and package proxies.

Use the view name in every filename and title. A drawing labeled only "top
view" is insufficient when two opposite faces are involved.

## Validation

After a narrow orientation correction:

1. Re-import the final STEP and check B-rep validity and solid count.
2. Check the bounding box against the accepted baseline.
3. Compare volume; investigate any change larger than the intended cutters can
   explain.
4. Validate STL watertightness and connected-body count.
5. Validate the 3MF archive and units.
6. Inspect both alignment and assembly renders.
7. Confirm that no proxy body was accidentally fused into the print solid.
8. Record the source-to-holder mapping and final coordinates in the manifest.

Use this prompt language when delegating a similar correction:

```text
Place the PCB flat with the named source face upward. State the sensor, socket,
long-axis, and short-axis directions in that view. Map only the PCB-face
features into the opposite holder mating face. Keep the validated optical axis,
C-mount, plate, depth stack, and all unrelated dimensions unchanged. Use photos
for orientation and measured values for geometry.
```
