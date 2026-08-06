# OpenHI Square Tube Connectors

Use this pattern for a square printed connector around a circular OpenHI/4F
tube, especially when the requested square envelope leaves very little wall at
the center of each face.

## Geometry Pattern

- Define the measured tube diameter, bore diameter, square envelope, and length
  as separate parameters.
- Keep the tube/print axis explicit.
- For a two-tube connector, use an annular center stop rather than a blocking
  disk.
- Make the stop support-friendly with straight chamfers: for the revised
  connector, a `40.2 -> 36 -> 40.2 mm` bore over a 4 mm axial base creates two
  45-degree faces.
- "Straight fillet" means chamfer or bevel. A fillet is rounded.

## Fasteners In A Thin Square Wall

Do not center a large radial fastener on a face without calculating local wall
thickness. A 42 mm square around a 40 mm bore has only 1 mm wall at the face
center. Shift the hole tangentially toward a corner and calculate:

- material length at the hole centerline;
- minimum material over the complete thread crest radius;
- outer edge ligament;
- clearance to adjacent faces and other holes.

For the revised 42 mm / 40.2 mm connector, an M6 crest radius of 3 mm at a
14.5 mm tangential offset gives about 4.5149 mm minimum material across the
full crest and about 7.0802 mm at the centerline.

## Printed Thread Pattern

Build threads in a stable local axis frame, then place them on each face:

1. Root/pilot cylinder.
2. Triangular tooth swept along a helix.
3. Extra half-pitch sweep at both ends.
4. Exact clipping to the final parent length.
5. Female: union pilot and tooth as one cutter, then subtract.
6. Male: union root and tooth.

Always export a single fit-test screw. For horizontal printed female M6 holes,
also export a tap-ready 5.0 mm pilot variant for an M6 x 1.0 tap.

True helices can be valid but slow to repair in Shapr3D because they introduce
B-spline faces. Keep the real thread for printing, and provide a smooth or
ring-groove Shapr target when downstream editability matters.

## Delivery

- Export connector and bolts separately in STEP/STL/3MF.
- Keep tube and screw proxies only in a fit-check assembly.
- Render the connector, fit assembly, center section, and exact bolt grid.
- Validate STEP solid count/B-rep/bbox, STL watertight components, 3MF package,
  and feature points.
- Create a timestamped print-ready run and sync it to
  `/home/lachlan/Nutstore Files/Projects/LabCanvas/<design>/<run>/`.

The full worked handoff lives in the LabCanvas repository at
`references/openhi-4f-square-tube-connector-cad-handoff-2026-08-06.md`.
