# Belt-driven hollow rotary stages

Use this reference for a simple optical rotary stage with a genuinely clear
center, a side-mounted stepper, a printed output pulley and a purchased metal
bearing. It is not a precision-stage certification or a universal motor mount.

## Reusable accepted example

Repository: `lachlanchen/AgInTi-LabCanvas`, project
`cad/designs/diy_hollow_rotary_stage_openhi_nema17/`.
Read its `README.md`, `FIELD_VALIDATION.md`, `fastener_contract.json` and current
run manifest before changing it. The owner reported on 2026-11-16 that the
run-7 WeNext print was assembled and works. Keep that evidence distinct from
measured accuracy, repeatability, payload or durability; none was reported.

The working example uses the named motor body from the owner's OpenHI STEP:
42 x 42 x 40 mm, 31 mm hole square, 22 mm front boss, 5 mm shaft and 22 mm
shaft projection. It is NEMA17 only, not an implicit 57 mm NEMA23 adapter.
Reuse the source B-rep and its face datum; do not redraw the motor from a frame
label or infer its electrical specification from CAD.

The core is a 6808 bearing, 40 x 52 x 7 mm, with a 39.9 mm fixed journal and
52.1 mm rotating seat. A 20T/120T GT2 drive uses a 300 mm pitch-length, 6 mm-wide
closed belt. The exact open-belt equation gives a 72.937066 mm center distance;
tension slots allow +/-3 mm. These are known example values, not defaults for
a different motor, belt or bearing.

## Mechanical decisions that matter

- Define the optical bore independently of the accessory aperture. This stage
  has a 30 mm bare passage and 24 mm with its 25.4 mm polarizer insert.
- Fix the bearing's inner race and retain the rotating outer race independently.
  A cap that squeezes both races together can lock an otherwise correct bearing.
  Avoid contact with shields, seals and corner radii.
- Keep the shaft for torque transmission, not as the main tray support. Separate
  the top carrier's drive geometry from the lower stand's height setting.
- Use belt pitch length and tooth profile, not outside belt circumference or an
  arbitrary scaled gear. The GT2 groove implementation derives from NopSCADlib
  and retains its GPL-3.0-or-later license and provenance.
- Distinguish in-plane motor yaw from a tilted mounting face. The installed
  example intentionally yaws the motor 10 degrees to clear Allen-key paths.
  Changing only the holes to zero degrees can leave the motor fitting correctly
  while its inner screws become inaccessible under the belt.
- A parallel-body alternative can bench-attach the motor to a removable plate,
  then use outboard plate clamps for tension. Check the complete sliding module
  at both travel limits and verify every clamp tool against the installed belt.
  The project's optional parallel-plate run is CAD-checked, not field-validated.
- An 85 mm tray underside does not imply 85 mm of empty space underneath.
  Audit the lowest rotating part, fixed carrier, cage rods, lamp/LCD stack,
  cable exits, screw heads and a full rotational envelope separately.

## Manufacturing and fasteners

For optical inserts, use the measured optic thickness rather than a placeholder
or approximate catalog value. The later GSP-25 update uses a measured 4.5 mm
optic and two intentionally shallow 2 mm recesses: the cap floats with a 0.5 mm
seam gap, or 0.7 mm with two 0.1 mm peripheral pads. Never tighten such a gap
closed against glass. Recess depth is not the overall part thickness; preserve
adequate retaining lips and fastener-pocket roofs. Document both-side contact,
aperture, radial fit, screw-tip clearance and the changed installed height.

Direct screws in printed plastic and through-bolts with nuts are both valid
choices; do not turn an owner's consideration of one into an exclusive rule.
A 2.5 mm pilot is a useful example for tapping M3 x 0.5, not a universal
"diameter minus 0.5" rule for self-tapping/thread-forming screws. Select the
pilot for the actual screw and material. Fit-test coupons are optional test
pieces, not installed parts; explain their purpose when they are delivered.

A broad unsupported flange was revised to a 6 mm-high, 45-degree annular
transition and a 0.2 mm radial lip. The cup prints upright. This reduced the
measured steep downward mesh area by about 85%; it did not prove that every
part is support-free or establish a print-success rate. Retain short nut-pocket
bridges and process-specific support requirements explicitly.

A successful SLS assembly does not validate a universal clearance. Keep the
reported 0.1 mm diametral bearing-seat allowance and journal reduction as the
accepted geometry. WeNext's quoted process tolerance was larger; measure a new
part and finish it gently if needed. Do not scale the assembly or hammer the
bearing.

Audit screw stack-ups rather than choosing a convenient assortment:
motor M3x6 plus 1 mm flat washers gives about 3 mm motor engagement;
rotor cap M3x12 is countersunk, so its stated length includes the head;
fixed retainer M2x14 and optic clip M2x5 have different lengths;
stand M4x16 changes to M4x20 only with the optional shim.
Plain captive nuts cannot be replaced by tall nyloc/flange nuts. M3 cap head
diameter is limited to 6.4 mm; check the actual supplier drawing, not just an
M3 or DIN/ISO label. Ordinary socket-head lengths exclude the head.

For purchasing, verify the exact variant, actual head shape, package count,
nuts and flat-washer dimensions. Reject mismatched variant titles and pictures.
An assortment is useful only if it covers the required lengths. Adding to an
authorized cart does not authorize checkout or payment. Record a single-click
intent, verify the exact resulting cart row, and check before retrying an
uncertain add. Reuse the logged-in dedicated browser; never mutate a hidden
shopping API or solve a CAPTCHA by bypassing it.

## Rebuild and deliver

The project provides `build_stage.py`, `build_parallel_variant.py`,
`render_stage.py` and `package_stage.py`. Use its existing CAD Python and Blender
runtimes. The optional builder preserves the accepted latest pointer; render an
explicit alternative with `render_stage.py -- --run RUN_DIR` under Blender.

Require valid reimported STEP solids, clear optical bore, moving/fixed checks,
belt/fastener/tool access, unchanged-part comparisons and grounded single-object
STL/STEP/3MF print files. Export factory parts separately from FDM ears, purchased
parts and diagnostic coupons. Sync the run's source, manifest, print files and
uncropped assembly/print renders to Nutstore LabCanvas. Put untested alternatives
under a clearly named optional-variant folder rather than replacing the proven
default. Preserve old runs and keep credentials, private installation photos,
order identities and raw cart history out of git.
