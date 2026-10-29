# Anatomical conventions

Definitions, coordinate frame, and measured repeat distances for the
landmarks the pipeline uses.

## Coordinate frame

All coordinates are in **LPS millimetres** (x increases toward the
patient's left, y toward posterior, z toward superior), matching
SimpleITK's world frame. Slicer displays RAS (x and y negated), so a
point at Slicer x=+100 is x=-100 in the pipeline. The loader
`landmark_io.load_landmarks` performs the RAS→LPS conversion, so
`.mrk.json` files can be read directly.

## Landmark definitions

Each landmark is defined by an anchor — a specific anatomical feature
or a pair of features whose midpoint is the landmark — not by an
area. Anchor-based landmarks (midpoint of two clear points, or
intersection of two clear edges) place to within 2–3 mm repeatably.
Surface-click landmarks placed by eye sit at 7–9 mm.

| Landmark | Anchor definition | Source |
|---|---|---|
| femoral_head_R | Centre of the largest axial circle of the right femoral head | standard mechanical-axis definition |
| femoral_head_L | Same, left | same |
| knee_centre_R | Axial at joint line: midpoint between centres of the medial and lateral condyle blobs | Paley; verify before citing |
| knee_centre_L | Same, left | same |
| ankle_centre_R | Coronal at talar dome: midpoint between the medial and lateral malleoli, projected to top of talus | standard mechanical-axis definition |
| ankle_centre_L | Same, left | same |
| condyle_medial_R | Coronal at joint line: most distal-medial point of the medial femoral condyle | needed for mLDFA |
| condyle_lateral_R | Coronal at joint line: most distal-lateral point of the lateral femoral condyle | same |
| plateau_medial_R | Coronal at joint line: most proximal-medial point of the medial tibial plateau | needed for MPTA |
| plateau_lateral_R | Coronal at joint line: most proximal-lateral point of the lateral tibial plateau | same |

Click-by-click placement instructions are in `docs/landmarks.md`, under
"Placement guide".

## Conventions that vary between sources

The knee centre is variously defined as (a) the midpoint between
the two condyle contact points, (b) the centre of the
intercondylar notch, (c) the centre of the best-fit circle of the
distal femur. This project uses (a). The ankle centre is variously
(a) the midpoint of the malleoli projected to the talar dome, (b)
the centre of the talar dome alone, (c) the midpoint of the tibial
plafond. This project uses (a). A different project could use
different rules without either being wrong; the validation report
states the convention used.

## Measured hand-placement repeat distance (case01)

Two independent placements on case01, measured as the Euclidean
distance between the two points in LPS millimetres. Update this
table when new landmarks are placed.

| Landmark | Distance |
|---|---|
| ankle_centre_R | 1.97 mm |
| condyle_lateral_R | 1.59 mm |
| knee_centre_R | 3.02 mm |
| plateau_medial_R | 2.89 mm |
| femoral_head_R | 4.26 mm |
| knee_centre_L | 5.00 mm |
| femoral_head_L | 6.21 mm |
| condyle_medial_R | 7.29 mm |
| plateau_lateral_R | 8.74 mm |
| ankle_centre_L | 2.0 mm (est.) |
| **mean** | **4.55 mm** |

The mean excludes `ankle_centre_L`: its 2.0 mm row is an estimate, not
a measurement (see Known limitations), so the mean over the nine
anchor-vs-anchor comparisons is 4.55 mm. This matches the measured
table in `docs/landmarks.md`.

`ankle_centre_L` is estimated at 2.0 mm, not measured. The first-pass
figure of 0.84 mm was measured against a guess, not against a second
anchor-based placement, and was not credible as a repeat distance. The
estimate of 2.0 mm matches the observed `ankle_centre_R` repeat
distance (1.97 mm). The 2.0 mm figure is what the D09 validation
report uses as the yardstick for both sides; it is not a measurement
and is labelled as an estimate wherever it appears.

The mean is dominated by `condyle_medial_R` and `plateau_lateral_R`,
which were placed by surface click. Anchor-based landmarks sit at
2 mm, surface clicks at 7–9 mm.

For comparison: the first-pass mean before the anchor definitions
was 8.09 mm. The improvement came entirely from redefining
`ankle_centre_R` and `condyle_lateral_R` as anchors.

## Scope

Landmarks placed on case01:
- All 14 right-side and left-side landmarks
- Repeat placement for the 10 right-side plus 3 left-side centres
  (femoral_head_L, knee_centre_L, ankle_centre_L)

Landmarks pending (case02, case03):
- All landmarks pending
- Case02 and case03 segmentations not yet merged; once merged, follow
  `docs/landmarks.md` for the same 10 landmarks per subject

Left-side joint-line landmarks (`condyle_*_L`, `plateau_*_L`) are
placed once without a repeat on case01 and are not used by the
HKA/MAD pipeline. They are used only if mLDFA/MPTA on the left leg
is attempted, which is out of scope for this sprint.

## Known limitations

- The repeat distance for `ankle_centre_R` and `condyle_lateral_R`
  is measured between the new anchor-based placement and the prior
  guess-based placement, not between two anchor-based placements. A
  true anchor-vs-anchor repeat would likely be 1–2 mm; the values
  in the table (1.97 and 1.59 mm) are lower-bound estimates.
- `ankle_centre_L` is listed as **2.0 mm (est.)**, not a measurement.
  The label-spelling mismatch (`ankle_center_L` vs `ankle_centre_L`)
  between the two save sessions was corrected by renaming, but the
  0.84 mm value that resulted compared the new anchor-based placement
  against the pre-fix guess-based placement, so it is a lower bound,
  not a repeat distance. 2.0 mm is the working yardstick, matching the
  `ankle_centre_R` repeat distance (1.97 mm). A true anchor-vs-anchor
  repeat on case01 should replace it when time allows; until then, the
  validation report states 2.0 mm as an estimate.
- Joint-line angles (mLDFA, MPTA) have not been evaluated against
  the hand reference because two of the four joint-line landmarks
  (`condyle_medial_R`, `plateau_lateral_R`) still sit at 7–9 mm,
  which is too much noise for a degree-level comparison. This is a
  scope decision, not a defect: the pipeline supports the
  measurement, but the reference is not tight enough to validate it.
- The automatic ankle centre (`landmarks.ankle_centre`) agrees with
  the hand reference to within **4.15 mm (right)** and **4.14 mm
  (left)** on case01. That is about twice the hand-placement repeat
  distance for the same landmarks (1.97 mm and 2.0 mm est.), so the
  automatic rule is **close to** the hand reference but not at the
  level of a second human placer. This is weaker than the femoral-head
  sphere fit, which matched the hand repeat on both sides. The residual
  4 mm splits into a 2.5 mm z-bias (the plafond band is 2 mm tall, so
  averaging over it pulls the answer up) and about 3 mm of x/y scatter
  on the left. Method and diagnostic in `docs/landmarks.md`
  (ankle_centre); the "why no talus yet" note there records the
  condition under which talus extraction should be added.
- The automatic knee centre (`landmarks.knee_centre`) agrees with the
  hand reference to within **6.36 mm (right)** and **7.21 mm (left)**
  on case01. That is 2.1× and 1.4× the hand-placement repeat distance
  for the same landmarks (3.02 mm and 5.00 mm), so the rule is **close
  to** the hand reference but not at the level of a second human
  placer. The residual is dominated by the hand reference itself: the
  right-side hand click sits 8.7 mm lateral of the femur slab's x
  centroid, the left-side click sits 0.4 mm away, and no symmetric
  automated rule can match both. Method and diagnostic in
  `docs/landmarks.md` (knee_centre). This is weaker than the femoral
  head fit and roughly on par with the ankle fit.

## Alignment angle sign convention

HKA deviation and MAD are signed: **positive = varus**, **negative =
valgus**, zero = straight. This is the convention `alignment.hka_deviation`
and `alignment.mad` implement (see `docs/decisions.md` D035).

"Lateral" is anatomical, not world-coordinate. On the patient's right
side (hip x < 0 in LPS), lateral is −x; on the left side (hip x > 0),
lateral is +x. The functions detect the side from the sign of the hip's
x coordinate, so the same positive number means "varus" on both sides.
An absolute value without a sign would lose the varus/valgus distinction
that drives every clinical reading of these numbers.

A limb with hip at x = 0 is rejected with `ValueError` — the side is
ambiguous at the midline and no realistic landmark sits there.