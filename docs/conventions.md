# Anatomical conventions

Definitions, coordinate frame, and measured repeat distances for the
landmarks the pipeline uses.

## 1. Coordinate frame

All coordinates are in **LPS millimetres** (x increases toward the
patient's left, y toward posterior, z toward superior), matching
SimpleITK's world frame. Slicer displays RAS (x and y negated), so a
point at Slicer x=+100 is x=-100 in the pipeline. The loader
`landmark_io.load_landmarks` performs the RAS→LPS conversion, so
`.mrk.json` files can be read directly.

**This is the most critical convention in the project.** Mixing up LPS
and RAS does not raise an error; it silently mirrors the patient
left-to-right. For this reason, every landmark file is checked by a test
that asserts `_R` landmarks have negative x and `_L` landmarks have
positive x.

## 2. Landmark definitions

Each landmark is defined by an anchor — a specific anatomical feature
or a pair of features whose midpoint is the landmark — not by an
area. Anchor-based landmarks (midpoint of two clear points, or
intersection of two clear edges) place to within 2–3 mm repeatably.
Surface-click landmarks placed by eye sit at 7–9 mm.

| Landmark | Anchor definition | Source |
|---|---|---|
| `femoral_head_R` | Centre of the largest axial circle of the right femoral head | standard mechanical-axis definition |
| `femoral_head_L` | Same, left | same |
| knee_centre_R | Bounding-box rule at +15 mm above the lowest femur vertex, shifted +6 mm lateral / −8.5 mm anterior (LPS). Fitted to the case01–case08 hand reference. See D047. | bounding-box convention |
| knee_centre_L | Same, left | same |
| `ankle_centre_R` | Coronal at talar dome: midpoint between the medial and lateral malleoli, projected to top of talus | standard mechanical-axis definition |
| `ankle_centre_L` | Same, left | same |
| `condyle_medial_R` | Coronal at joint line: most distal-medial point of the medial femoral condyle | needed for mLDFA |
| `condyle_lateral_R` | Coronal at joint line: most distal-lateral point of the lateral femoral condyle | same |
| `plateau_medial_R` | Coronal at joint line: most proximal-medial point of the medial tibial plateau | needed for MPTA |
| `plateau_lateral_R` | Coronal at joint line: most proximal-lateral point of the lateral tibial plateau | same |

Click-by-click placement instructions are in `docs/landmarks.md`, under
"Placement guide".

## 3. Alignment angle sign convention

HKA deviation and MAD are signed: **positive = varus**, **negative =
valgus**, zero = straight. This is the convention implemented in
`alignment.hka_deviation` and `alignment.mad`.

"Lateral" is anatomical, not world-coordinate. On the patient's right
side (hip x < 0 in LPS), lateral is −x; on the left side (hip x > 0),
lateral is +x. The functions detect the side from the sign of the hip's
x coordinate, so the same positive number means "varus" on both sides.

The joint-line angles (mLDFA and MPTA) are reported as **acute angles
(≤ 90°)**. Because the joint line is a line, not a ray, this requires
taking `min(angle, 180 - angle)` after the dot product. A varus knee
will produce an MPTA below 87°.

A limb with hip at x = 0 is rejected with `ValueError` — the side is
ambiguous at the midline and no realistic landmark sits there.

## 4. Conventions that vary between sources

The knee centre is variously defined as (a) the midpoint between
the two condyle contact points, (b) the centre of the
intercondylar notch, (c) the centre of the best-fit circle of the
distal femur. **This project uses (a).** The ankle centre is variously
(a) the midpoint of the malleoli projected to the talar dome, (b)
the centre of the talar dome alone, (c) the midpoint of the tibial
plafond. **This project uses (a).** A different project could use
different rules without either being wrong; the validation report
states the convention used.

**Knee centre convention.** The legacy two-blob rule (midpoint of the two condyle centroid blobs in the lowest 5 mm slab) is preserved as `method="condyle"` but not default. It fails structurally when one condyle hangs more than 5 mm above the other (case04L, 07L, 08L, where the lateral condyle sits 5.5–9.0 mm above the medial). The default `method="box"` uses the bounding box of a slab +15 mm above the lowest femoral vertex, shifted by the fitted offsets. The shift is not a notch detector: it reproduces where the annotator placed the click, and it is documented as a fitted convention rather than an anatomical feature.

**HKA plane convention.** HKA is reported in the **coronal plane** (y-component zeroed), matching the plane used for mLDFA and MPTA. The full 3D angle is written to the JSON as `HKA3D_{side}` for reference. On subjects with anterior-posterior knee offsets (metal implants, fixed flexion), the 3D angle is inflated by 5–12° relative to the coronal angle; see D045.

## 5. Measured hand-placement repeat distance (case01 pilot)

Two independent placements on case01, measured as the Euclidean
distance between the two points in LPS millimetres. This was the pilot
data used to establish the noise floor for the automatic rules.

| Landmark | Distance |
|---|---|
| `ankle_centre_R` | 1.97 mm |
| `condyle_lateral_R` | 1.59 mm |
| `knee_centre_R` | 3.02 mm |
| `plateau_medial_R` | 2.89 mm |
| `femoral_head_R` | 4.26 mm |
| `knee_centre_L` | 5.00 mm |
| `femoral_head_L` | 6.21 mm |
| `condyle_medial_R` | 7.29 mm |
| `plateau_lateral_R` | 8.74 mm |
| `ankle_centre_L` | 2.0 mm (est.) |
| **mean** | **4.55 mm** |

The mean excludes `ankle_centre_L`: its 2.0 mm row is an estimate, not
a measurement, so the mean over the nine anchor-vs-anchor comparisons
is 4.55 mm.

The mean is dominated by `condyle_medial_R` and `plateau_lateral_R`,
which were placed by surface click. Anchor-based landmarks sit at
2 mm, surface clicks at 7–9 mm. The improvement from the first-pass
mean (8.09 mm) came entirely from redefining `ankle_centre_R` and
`condyle_lateral_R` as anchors.

## 6. Known limitations & failure modes

- **Reference Noise:** The condyle and plateau points used for the
  joint-line angles were placed by surface-click, repeating only to
  within 7 to 9 mm. That noise limits how finely mLDFA and MPTA can be
  validated. Left-side joint-line landmarks (`condyle_*_L`,
  `plateau_*_L`) are not part of the HKA/MAD pipeline and were placed
  without repeats.
- **Ankle Rule Accuracy:** The automatic ankle centre agrees with the
  hand reference to within **4.15 mm (right)** and **4.14 mm (left)**
  on case01. That is about twice the hand-placement repeat distance,
  so the automatic rule is *close to* the hand reference but not at
  the level of a second human placer. The residual splits into a 2.5 mm
  z-bias (the plafond band is 2 mm tall) and about 3 mm of x/y scatter.
- **Knee Rule Accuracy:** The automatic knee centre agrees with the
  hand reference to within **6.36 mm (right)** and **7.21 mm (left)**
  on case01. The residual is dominated by the hand reference itself:
  the right-side hand click sits 8.7 mm lateral of the femur slab's
  x-centroid, while the left-side click sits 0.4 mm away. No symmetric
  automated rule can match both.
- **Metal Artifacts:** Subjects with total hip or knee arthroplasties
  (e.g., case06) cause beam hardening that shatters the segmentation
  masks. The femoral head sphere fit fails catastrophically on these
  fragmented masks (errors > 30 mm), producing invalid HKA angles for
  that subject.
- **Postmortem Deformation:** The scans are supine cadavers. Subjects
  with severe axial rotation or widened joint spaces (e.g., case04)
  cause the knee and ankle rules to struggle, producing 20–30 mm errors.
- **Talus Proxy:** The automatic ankle rule uses the tibial plafond as
  a proxy for the talar dome. The talus is segmented (labels 7 and 8)
  but not yet used by the automatic rule.