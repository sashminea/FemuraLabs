# Landmarks

Everything about hand-placed and automatically-detected landmarks: the
traps that cost hours on case01, the definitions and click-by-click
placement rules for the ten landmarks, the measured hand repeat
distances, and the algorithm that finds the femoral head centre without
a human.

Read the pitfalls first. Every one of them is a silent error — the
pipeline produces a mirrored mesh, a wildly wrong angle, or a
physiologically impossible radius with no error message. Catching them
before they compound is the difference between a defensible validation
report and one that gets torn apart in review.

## Pitfalls in landmark placement and coordinate handling


1. **Slicer's default axial view is radiological.** Screen-right is the patient's **left**. When you place a landmark labeled `_R`, it must lie on the side that appears on the **left of the screen** in Slicer's axial view. If you label screen-right as `_R`, every left/right pair is swapped and the pipeline returns mirrored results. See "The left/right confusion" for how this was discovered.

2. **Slicer saves `.mrk.json` in LPS, not RAS.** The file declares `"coordinateSystem": "LPS"`. Do not negate x and y when reading a Slicer `.mrk.json` unless the file explicitly says `"RAS"`. The loader `landmark_io.load_landmarks` handles both cases by reading the field.

3. **The pipeline uses LPS millimetres** (SimpleITK's world frame). Slicer displays RAS, so any coordinate read from Slicer's status bar must be mentally negated in x and y before comparing it with the pipeline.

4. **Surface clicks have a 7–9 mm repeat distance; anchor-based clicks have 2–3 mm.** A surface click is a single point on a smooth curve. An anchor-based click is the midpoint of two clear points or the intersection of two clear edges. Every landmark definition below that is anchor-based is anchor-based for this reason. When the guide says "midpoint", click the two anchors first and compute the midpoint — do not eyeball it.

5. **The femoral head is the medial-most spherical feature of the proximal femur.** A sphere fit to the whole proximal end also captures the greater trochanter, which is not spherical and pulls the centre laterally. Constrain the fit by both z (superior) and x (medial). See "Femoral head centre".

6. **The bottom of the tibia mask is not the ankle joint.** The very bottom of the shinbone is the pointed tip of the medial malleolus (the inner ankle bone). The actual joint surface is the plafond, a flat band about 14 mm higher. A slab at the very bottom samples the tip and comes out 14 mm too low, 15 mm too far forward, and 10 mm too far inward — a 22–26 mm error on case01 with no warning. Find the plafond as the widest cross-section in the bottom 30 mm of the tibia, not as the bottom-most slab.

7. **The fit radius is the diagnostic.** An adult femoral head has a radius of 17–25 mm. A fit that returns 30+ mm is not the head. Assert the range in the test; do not compare against a hand-placed point until the radius is plausible.

8. **"Automatic error < hand repeat distance" is success.** The hand reference is not perfect either. If the automatic method agrees with the hand point to within the hand-placement repeat distance for the same point, the method is at the level of a second human placer. That is the strongest possible outcome for a single-subject reference, and it is what D08 achieved.

9. **`data/ref/` is gitignored.** Landmark files contain patient-specific coordinates and stay on disk. Only the placement rules, repeat distances, and algorithm code are committed.

10. **The pipeline does not need every landmark.** HKA and MAD use only the six centres (hip, knee, ankle per side). Joint-line angles (mLDFA, MPTA) also need the four condyle/plateau points, but those four are surface clicks with higher noise and are not part of the validated pipeline.

11. **The talus is a visual reference, not a landmark.** As of case03, the merged segmentation includes labels 7 and 8 (`Talus_R`, `Talus_L`). This was added because `ankle_centre` is defined as the midpoint of the malleoli projected to the **top of the talus**. The hand-placer should use the talus mask to visually confirm the joint line, but the talus itself is not a hand-placed landmark. The D09 rule (`ankle_centre`) still uses the tibia and fibula; the talus is only for human verification.

---

## The left/right confusion

This trap deserves its own section because it consumed most of a
session and is not obvious until you have been bitten by it.

In Slicer's default axial view you are looking at the patient from the
feet, as if you were the scanner. This is radiological convention. The
consequence: **the patient's right side appears on the left of the
screen, and the patient's left side appears on the right of the
screen.** This is the opposite of what "screen-right" suggests.

On the first placement session for case01, `_R` landmarks were placed
on the screen-right side. The result was that the file ended up with:

- `femoral_head_R` at LPS x = +94 (should be negative)
- `femoral_head_L` at LPS x = −71 (should be positive)
- Both knees on the same side of the body
- `test_femoral_head_right_agrees_with_hand_placement` failing with a
  290 mm error against the mask centroid (which has the correct sign
  from the mask, not from the placement)

The 290 mm error was not a placement error in mm; it was a 2×156 sign
flip in the y coordinate. Nothing crashed; the numbers just silently
meant the opposite of what the labels said.

**The fix** is to swap every `_R` and `_L` label in both the primary
and repeat `.mrk.json` files after re-verifying that all placements are
on the correct physical side of the body. That is a one-time correction
of the files. The permanent prevention is that every future placement
session checks the R/L labels in the corner of Slicer's axial view
*before clicking*, and every new landmark file is checked by a test
that asserts `femoral_head_R.x < 0` and `femoral_head_L.x > 0` in LPS.

The verification command after every placement session:

```python
from femuralabs.toolkit.landmark_io import load_landmarks
h = load_landmarks("data/ref/landmarks_case0X.mrk.json")
assert h["femoral_head_R"][0] < 0, "femoral_head_R is on the wrong side"
assert h["femoral_head_L"][0] > 0, "femoral_head_L is on the wrong side"
assert h["ankle_centre_R"][0] < 0, "ankle_centre_R is on the wrong side"
assert h["ankle_centre_L"][0] > 0, "ankle_centre_L is on the wrong side"
```

If any of the four assertions fails, do not proceed. Re-check the file
before running any downstream stage.

## Landmark definitions

All coordinates are in **LPS millimetres**, matching SimpleITK's world
frame. Slicer shows RAS (x and y negated), so a point at Slicer x=+100
is x=−100 in the pipeline. The loader performs the RAS→LPS conversion
when the file declares RAS and leaves LPS files alone.

| Landmark | Anchor definition | Used for |
|---|---|---|
| `femoral_head_R` | Centre of the best-fit sphere to the medial hemisphere of the right femoral head | femoral mechanical axis |
| `femoral_head_L` | Same, left | femoral mechanical axis |
| `knee_centre_R` | Axial at joint line: midpoint between the centres of the medial and lateral condyle blobs | both mechanical axes |
| `knee_centre_L` | Same, left | both mechanical axes |
| `ankle_centre_R` | Coronal at talar dome: midpoint between the medial and lateral malleoli, at the top of the talus | tibial mechanical axis |
| `ankle_centre_L` | Same, left | tibial mechanical axis |
| `condyle_medial_R` | Coronal at joint line: most distal-medial point of the medial femoral condyle (surface click; 7–9 mm repeat) | mLDFA |
| `condyle_lateral_R` | Coronal at joint line: most distal-lateral point of the lateral femoral condyle (surface click) | mLDFA |
| `plateau_medial_R` | Coronal at joint line: most proximal-medial point of the medial tibial plateau (surface click) | MPTA |
| `plateau_lateral_R` | Coronal at joint line: most proximal-lateral point of the lateral tibial plateau (surface click) | MPTA |

**Conventions that vary between sources.** The knee centre is variously
defined as (a) the midpoint between the two condyle contact points,
(b) the centre of the intercondylar notch, (c) the centre of a circle
fit to the distal femur. **This project uses (a).** The ankle centre is
variously (a) the midpoint of the malleoli projected to the talar dome,
(b) the centre of the talar dome alone, (c) the midpoint of the tibial
plafond. **This project uses (a).** A different project may use
different rules without either being wrong; the validation report
states the convention used.

## Placement guide

Click-by-click instructions for placing the ten landmarks. Generated
from annotated screenshots of case01 by Gemini, then verified on case01
by placing each landmark multiple times and measuring repeat distance
(see "Measured repeat distance" below).

Use this guide to place landmarks on any future subject, so that
placement is consistent. Wording is plain on purpose; each step names
what to look for in the image.

**Conventions used in this guide:**

- **Primary view** — the 2D view to work in first. Chosen for each
  landmark because it makes the reference features most visible.
- **Secondary view** — the view that confirms placement.
- **Safe cortical offset** — place the point slightly inside the bone
  boundary, not on the very edge of the mask. Keeps the point inside
  the mesh after marching cubes, so distance and volume calculations
  do not see a point the mesh does not contain. 1–2 voxels of inset is
  enough.
- **Midpoint** — arithmetic average of two clicked points. When a
  landmark is defined as a midpoint, click the two anchors first, then
  place the landmark at their average. This is why anchor-based
  landmarks reach 2 mm repeatability and surface-click landmarks sit
  at 7–9 mm.
- **Anatomical sides** — see "The left/right confusion" above. In
  Slicer's default axial view, screen-right is the patient's left.
  `_R` landmarks must be on the side that appears on the **left of
  the screen**. Check the corner labels before every click.

### `femoral_head_R`

**Primary view:** Axial. **Secondary view:** Coronal and sagittal.

1. Scroll up in the axial view until you see the round, ball-shaped
   top of the right thigh bone (the femoral head) nested inside the
   pelvis socket.
2. Scroll up and down slightly to find the slice where the ball
   shape has its largest diameter.
3. The point you want is the geometric centre of that circular
   cross-section — not the top edge, not the neck, the centre.
4. Click there.

**Verification:** Coronal — the point sits dead in the middle of the
hip ball, not on its surface. Sagittal — same.

**Common mistakes:**
- Placing on the cortical edge rather than the centre — visible in
  coronal as a point at the top or side of the ball.
- Placing at the neck-base junction — visible in axial as a slice just
  below the largest circle.
- Wrong side — check the R/L corners of the axial view.

<img width="1050" height="862" alt="image" src="https://github.com/user-attachments/assets/8fba6442-f57c-46e5-8490-0b88a65494e1" />


### `femoral_head_L`

Same steps, left side. Mirror image.

<img width="1033" height="862" alt="image" src="https://github.com/user-attachments/assets/e9f66c4d-734f-4728-bace-84d48b92ea8f" />


### `knee_centre_R`

**Primary view:** Axial. **Secondary view:** Coronal.

1. Scroll vertically in the axial view to the middle of the right
   knee joint, where the thigh bone (femur) meets the shin bone
   (tibia).
2. Locate the intercondylar notch — the deep, U-shaped arch that
   separates the two lower knuckles of the thigh bone.
3. Find the geometric centre of this arch in the cross-section.
4. Click at the centre of the notch opening, with the safe cortical
   offset.

**Verification:** Coronal — the point sits in the middle of the knee
joint space between femur and tibia, at the level of the joint line.

**Common mistakes:**
- Placing at the very top of the trochlear groove (too proximal) —
  visible in coronal as a point above the joint space.
- Placing at the tibial plateau level (too distal) — visible in
  coronal as a point below the joint space.
- Wrong side.

<img width="1042" height="862" alt="image" src="https://github.com/user-attachments/assets/996e7d10-9c17-45c1-84c6-086cdc84ea1b" />


### `knee_centre_L`

Same steps, left side.

<img width="1050" height="862" alt="image" src="https://github.com/user-attachments/assets/8d72d01a-224c-43b8-ba78-164e803e1898" />


### `ankle_centre_R`

**Primary view:** Coronal. **Secondary view:** Axial.

1. Scroll in coronal until you find the central slice of the
   tibiotalar joint, where the shin bone meets the talus (the ankle
   bone that sits just below the shin bone).
2. Identify the medial malleolus (the inner bump of the ankle) and
   the lateral malleolus (the outer bump of the ankle).
3. Compute the horizontal midpoint between the innermost edge of
   the medial malleolus and the outermost edge of the lateral
   malleolus.
4. Locate the superior cortical surface of the talar dome (the
   smooth curved top of the ankle bone).
5. Click at the horizontal midpoint, resting on the top surface of
   the talar dome, just below the joint gap.

**Verification:** Axial — the point sits centrally within the
cross-sectional body of the talus.

**Common mistakes:**
- Floating in the joint gap — visible in coronal as a point suspended
  in the dark space above the talus.
- Off-centre anterior/posterior — visible in axial as a point at the
  front or back of the talus body.
- Wrong side.

<img width="1052" height="862" alt="image" src="https://github.com/user-attachments/assets/4f6caa7c-5cc4-45e6-aba2-223a491b97f4" />


### `ankle_centre_L`

Same steps, left side.

<img width="1030" height="862" alt="image" src="https://github.com/user-attachments/assets/359d887f-793f-4e2f-af3a-b79583f21df7" />


### `condyle_medial_R`

**Primary view:** Coronal. **Secondary view:** Axial.

1. In coronal, scroll to the widest section of the knee joint.
2. Focus on the medial (inner) knuckle of the right thigh bone
   (the yellow mask in Slicer's segmented view), facing toward the
   other leg.
3. Find the lowest (most distal) surface point of this inner
   knuckle where it meets the joint space.
4. Find the innermost boundary edge of the same knuckle.
5. Click at the intersection of lowest and innermost, with the
   safe cortical offset.

**Verification:** Axial — the point sits on the medial-most
boundary of the right thigh bone.

**Common mistakes:**
- Placed on the lateral condyle by mistake — visible in axial as a
  point on the wrong side of the femur.
- Floating above the joint line — visible in coronal as a point not
  touching the condyle surface.

<img width="1032" height="862" alt="image" src="https://github.com/user-attachments/assets/2186a7f8-bd16-46f3-8eb2-287980fa848e" />



**Anchor note:** this landmark is defined as "the intersection of two
surface directions". If it repeats badly, the fix is to click the
medial-most and lateral-most points on the condyle's joint-line edge
separately, then use their midpoint as the landmark. That converts the
surface click into a midpoint anchor.



### `condyle_lateral_R`

Same steps as `condyle_medial_R`, on the lateral (outer) side. Faces
away from the other leg.


<img width="1037" height="862" alt="image" src="https://github.com/user-attachments/assets/8c5786ff-f37d-450f-9d97-3a3cc37d8e2e" />

### `plateau_medial_R`

**Primary view:** Coronal. **Secondary view:** Axial.

1. In coronal, scroll to the widest section of the knee joint.
2. Focus on the medial (inner) side of the right shin bone (blue
   mask), facing toward the other leg.
3. Find the highest (most proximal) point on the flat top rim of
   the medial tibial plateau, right against the joint line.
4. Find the innermost medial edge of this platform.
5. Click at the top-inner corner, with the safe cortical offset.

**Verification:** Axial — the point sits on the innermost boundary of
the upper right shin bone.

**Common mistakes:**
- Placed on the lateral plateau by mistake.
- Floating in the joint gap above the plateau.

<img width="1032" height="862" alt="image" src="https://github.com/user-attachments/assets/270db2a3-2e6a-4717-82e6-dbb7a803b8fd" />

### `plateau_lateral_R`

**Primary view:** Coronal. **Secondary view:** Axial.

1. In coronal, scroll to the widest section of the knee joint.
2. Focus on the lateral (outer) side of the right shin bone (blue
   mask), facing away from the other leg.
3. Find the highest point on the flat top rim of the lateral
   tibial plateau.
4. Find the outermost lateral edge of this platform where the bone
   curves down.
5. Click at the top-outer corner, with the safe cortical offset.

**Verification:** Axial — the point sits on the outer-most lateral
edge of the upper right shin bone.

**Common mistakes:**
- Placed on the inner side by mistake.
- Floating in the knee gap.
- Sunk too deep into the bone centre rather than on the outer
  boundary.

<img width="1024" height="847" alt="image" src="https://github.com/user-attachments/assets/6db79dcc-23ba-4148-ab03-f3b3098fd503" />



### Left-side surface landmarks (`condyle_*_L`, `plateau_*_L`)

Same steps as the right side, mirror image. These are placed once
without a repeat and are not used by the HKA/MAD pipeline; they are
needed only if mLDFA/MPTA on the left leg is attempted.

## Measured hand-placement repeat distance (case01)

Two independent placements of the same landmarks on case01, measured
as the Euclidean distance between the two points in LPS millimetres.
The first pass had the left/right labels swapped; the numbers below are
from the corrected files.

| Landmark | Distance | Notes |
|---|---|---|
| ankle_centre_R | 1.97 mm | anchor: midpoint of malleoli |
| condyle_lateral_R | 1.59 mm | anchor: midpoint of joint-line edges |
| knee_centre_R | 3.02 mm | |
| plateau_medial_R | 2.89 mm | |
| femoral_head_R | 4.26 mm | |
| knee_centre_L | 5.00 mm | |
| femoral_head_L | 6.21 mm | |
| condyle_medial_R | 7.29 mm | surface click |
| plateau_lateral_R | 8.74 mm | surface click |
| **mean (9)** | **4.55 mm** | |

Landmarks with an arithmetic anchor (midpoint of two clear points)
reach 2 mm repeat distance. Surface-click landmarks sit at 7–9 mm. The
mean is dominated by the two surface-click landmarks; both are
acceptable for the joint-line angles (about 1 degree uncertainty) but
are not used for HKA.

First-pass mean before anchor definitions was 8.09 mm. The improvement
came entirely from redefining `ankle_centre_R` and `condyle_lateral_R`
as anchor-based (two-point midpoint) rather than surface-click.

## Saving and loading

Save in Slicer as `landmarks_case0X.mrk.json` and copy to `data/ref/`.
The file is gitignored. The loader `landmark_io.load_landmarks` reads
it and returns `{name: (x, y, z)}` in LPS millimetres. It respects the
file's `coordinateSystem` field: RAS files are negated in x and y to
give LPS, LPS files are returned unchanged.

Run this check after every placement session, before committing to the
pipeline:

```python
from femuralabs.toolkit.landmark_io import load_landmarks
h = load_landmarks("data/ref/landmarks_case0X.mrk.json")
for name in ("femoral_head_R", "knee_centre_R", "ankle_centre_R"):
    assert h[name][0] < 0, f"{name} is on the wrong side (positive LPS x)"
for name in ("femoral_head_L", "knee_centre_L", "ankle_centre_L"):
    assert h[name][0] > 0, f"{name} is on the wrong side (negative LPS x)"
print("all sides correct")
```

## Automatic detection

Three landmarks are estimated from the meshes: femoral head centre,
ankle centre, knee centre. Each has a rule, a measured error against
the case01 hand reference, and a diagnostic function that prints the
intermediate values a failure points at. All three are weaker than a
second human placer on at least one side — that is documented per
rule, not hidden. Only `femoral_head_centre` matches the hand repeat
distance on both sides.

### Femoral head centre — `landmarks.femoral_head_centre`

Given a femur mesh (world millimetres), returns `(centre, radius, rms)`.
The centre is compared against `femoral_head_R` / `femoral_head_L` to
measure the automatic method.

**Algorithm.** Two constraints stacked:

1. **Superior region**: keep only the top 25 percent of the mesh by z.
   Both the head and the greater trochanter are superior, so this
   narrows the search but does not isolate the head.
2. **Medial window**: keep only vertices within `medial_window_mm`
   (default **20 mm**) of the medial-most x. The head is the
   medial-most feature, so this window captures the medial hemisphere
   of the head. Larger windows start to include the trochanter, which
   is not spherical, and pull the fit radius up.

Then fit a sphere by linear least-squares (see "Why the fit works"
below), trim the worst 20 percent of residuals, refit, three iterations.

**On case01 with `medial_window_mm=20`:**

| Side | Fit centre | Hand centre | Error | Radius |
|---|---|---|---|---|
| R | (−73.3, −145.4, 1085.2) | (−70.8, −148.1, 1084.5) | 3.81 mm | 18.3 mm |
| L | (92.5, −156.8, 1104.5) | (94.2, −156.3, 1100.0) | 4.82 mm | 20.4 mm |

Both errors are **inside the hand-placement repeat distance** for the
same point (4.26 and 6.21 mm). The automatic method is at the level of
a second human placer.

### Why the fit works — the linear trick

The equation of a sphere is `(x−a)² + (y−b)² + (z−c)² = r²`, where
`(a,b,c)` is the centre and `r` is the radius. Expand and rearrange:

```
x² + y² + z² = 2ax + 2by + 2cz + (r² − a² − b² − c²)
```

The right-hand side is linear in four unknowns `(a, b, c, d)` where
`d = r² − a² − b² − c²`. For each surface vertex you get one linear
equation. Stack `N` vertices, solve an `N × 4` system with
`np.linalg.lstsq`. That is why `fit_sphere` recovers the centre to
`1e-6` on noise-free synthetic data with no iteration — it is a linear
least-squares problem, not an iterative sphere-fit.

The wrapper `femoral_head_centre` is what makes this work on a real
femur: it narrows the region so that the fit is looking at the head,
not at head+neck+trochanter averaged together.

### Extending to case02 and case03

The **20 mm medial window is a starting point, not a universal
constant.** It works on case01 because the femoral head is a typical
adult size. On a smaller or larger head it may need adjusting. The
diagnostic sweep that determined it for case01 is:

```python
for w in (15, 17, 18, 20, 22, 25, 28, 30, 35, 40):
    c, r, _ = femoral_head_centre(verts, medial_window_mm=w)
    print(f"w={w:>2}: radius={r:.1f} mm")
```

On case01, the fit radius stays in the anatomical range (17–25 mm) up
to about 20 mm and jumps to 30+ mm above 25 mm. Look for the same
transition point on a new subject: the window just below the jump from
"head-sized" radius to "head-plus-trochanter" radius. Then hard-code
that window for that subject (per-subject parameter), or extend
`femoral_head_centre` to sweep windows internally and return the first
plausible fit.

**What to do if a subject fails:**

- Fit radius comes out under 17 mm on every window → the medial window
  is too tight (a very small head, or mask under-segmentation). Try
  22, 25, 28 mm windows.
- Fit radius comes out over 25 mm on every window → the medial window
  is too generous (a very large head, or mask including the
  trochanter). Try 15, 17, 18 mm windows.
- Fit fails with "medial window contains only N vertices" → the mask
  truncates the medial side (rare). Check the mask in Slicer.
- Fit fails with "proximal region has only N vertices" → the mesh is
  truncated at the top. Check that the full femur was included in the
  segmentation.

The extension from case01 to case02/03 should take about 5 minutes per
subject, not 30: extract the mesh, run the diagnostic sweep, pick the
window, note it in this file. The algorithm code does not need to
change.


### Ankle centre — `landmarks.ankle_centre`

Given the tibia and fibula meshes (world millimetres), returns
`(centre, info)` where `info` carries `plafond_z`, `medial_x`,
`lateral_x`. The centre is compared against `ankle_centre_R` /
`ankle_centre_L` to measure the automatic method.

**Picture the bottom of the shinbone.** Like an upside-down wine
glass. The very bottom is a narrow point — the tip of the inner ankle
bone (the medial malleolus). Going up, the bone flares out into the
wide body of the shinbone. The flat bottom of that body, where it
sits on the ankle bone (talus), is the plafond. The hand-placer
clicks the plafond. The old draft sampled the very bottom, which is
the tip, 14 mm below the plafond — hence a 22–26 mm error with no
warning sign in the code.

**Algorithm.** Three steps, no per-subject tuning:

1. **Find the plafond.** In the bottom 30 mm of the tibia, bin
   vertices into 2 mm z-bands and measure each band's x-extent.
   The widest band is the plafond. On case01 the plafond is a
   flat-topped band 3.5–7 mm tall, at z ≈ 265 (R) and z ≈ 287 (L),
   within 2 mm of the hand clicks.
2. **Take the two malleoli at the plafond level.** At
   `plafond_z ± 1 mm`, the medial edge of the tibia is the medial
   malleolus; the lateral edge of the fibula is the lateral
   malleolus.
3. **Midpoint is the ankle centre.** x = mean of the two edges;
   y = mean of the tibia verts at that level (the plafond centroid
   sits directly over the talar dome); z = plafond_z.

This is rule (a) from `docs/conventions.md`: "midpoint between the
medial and lateral malleoli, projected to the top of the talus". The
projection to the talar dome is approximated by the plafond
centroid's y; we do not extract the talus mesh. See "Why no talus
yet" below.

**Parameters.** `search_top_mm=30.0`, `bin_mm=2.0`. The 30 mm is a
safety margin: the plafond is ~14 mm above the malleolar tip, so 30
gives 16 mm of slack above the plafond. Both are shape assumptions
about adult anatomy, not numbers tuned to case01's hand reference.

**On case01 with the default parameters:**

| Side | Fit centre | Hand centre | Error | Hand repeat |
|---|---|---|---|---|
| R | (−53.7, −79.4, 307.7) | (−52.4, −76.4, 305.2) | 4.15 mm | 1.97 mm |
| L | (92.8, −89.7, 324.1) | (90.5, −89.9, 320.6) | 4.14 mm | ~2.0 mm |

Both errors are about **2× the hand repeat distance** — close to the
hand reference, but not at the level of a second human placer. This
is a weaker result than `femoral_head_centre` (which matched the
hand repeat). The residual 4 mm splits into a 2.5 mm z-bias (the
plafond band is 2 mm tall, so averaging over it pulls the answer up)
and about 3 mm of x/y scatter on the left.

**Why no talus yet.** The rule that `conventions.md` promises uses
the talus. We do not extract the talus mask. On case01 the plafond
centroid's y lands within 3 mm of the hand click — the plafond is
already a good proxy for the talar dome directly beneath it. The
R-side dy is exactly −3.0 mm, at the boundary of "revisit if it
gets worse". Adding the talus is deferred until a subject shows
dy > 3 mm; the pipeline is honest about it in the validation report.

**Extending to case02 and case03.** Same rule, same parameters. No
per-subject tuning is expected — the plafond is anatomical, not
patient-specific. If a subject's fit fails, the diagnostic is the
`info` dict, not a sweep:

- `plafond_z` within 3 mm of `tibia_z_min` → the bottom 30 mm is
  truncated. Check the mesh covers the full tibia.
- `plafond_z` > 30 mm above `tibia_z_min` → the widest band is not
  the plafond but a metaphyseal flare higher up. Widen the search
  band or check the mask for a spur.
- `medial_x` on the wrong side of `lateral_x` → the side-detection
  heuristic (`np.median(tibia_verts[:, 0]) < 0`) is confused.
  Unlikely on a full-limb scan but the assertion catches it.
- Error > 6 mm with all three intermediates sane → the assumption
  "plafond centroid ≈ talar dome" is the part to question. That is
  the trigger to add the talus mesh.

### Knee centre — `landmarks.knee_centre`

Given the femur mesh (and the tibia mesh, accepted for signature
compatibility but not used), returns `(centre, info)` where `info`
carries `condyle_medial`, `condyle_lateral`, and `slab_mm`. The centre
is compared against `knee_centre_R` / `knee_centre_L` to measure the
automatic method.

**Rule.** Two-condyle midpoint at the distal femur, per rule (a) in
`docs/conventions.md`: "midpoint between centres of the medial and
lateral condyle blobs". Algorithm:

1. Take the bottom 5 mm of the femur mesh (the distal condyles at the
   joint line).
2. Split that slab at its own x mid-point.
3. Each half's vertex centroid approximates one condyle blob.
4. The knee centre is the mean of the two blob centroids.

Nothing is tuned per subject. `slab_mm=5.0` is the only parameter, and
it matches the level at which the hand click was placed.

**The previous draft was wrong, and why.** The draft averaged the
*whole* distal femur cross-section with the *whole* proximal tibia
cross-section. Two independent biases made it 10–14 mm off:

- The tibia's top cross-section sits ~14 mm anterior of the femur's
  bottom cross-section, so averaging the two pulls the result
  posterior. On case01 both sides showed dy = +10 mm, same direction,
  same magnitude — a signature of a systematic averaging error, not
  noise.
- The whole femur cross-section's centroid drifts toward the medial
  condyle, which is larger. The hand click is at the mid-point of the
  two condyles, not at the cross-section's centroid. The split-at-mid
  rule corrects this.

The diagnostic pattern was: (a) split into mesh-vs-mask and
slab-5mm-vs-20mm; (b) dy was +10 mm on all four combinations, killing
the vertex-density and slab-thickness explanations; (c) femur-only vs
tibia-only vs averaged showed the tibia was the source of dy; (d)
two-condyle split matched rule (a) and cut the error in half.

**On case01 with `slab_mm=5.0`:**

| Side | Fit centre | Hand centre | Error | Hand repeat |
|---|---|---|---|---|
| R | (−66.8, −123.8, 661.4) | (−71.2, −127.9, 663.3) | 6.36 mm | 3.02 mm |
| L | (81.1, −107.5, 681.9) | (81.9, −114.0, 685.0) | 7.21 mm | 5.00 mm |

**The residual is the hand reference, not the rule.** On the right,
the hand click sits 8.7 mm lateral of the femur slab's x-centroid; on
the left, it sits 0.4 mm. The two hand clicks were placed relative to
their own condyles by an inconsistent amount, and no symmetric
automated rule can match both to under 8 mm. The errors of 6.36 mm (R)
and 7.21 mm (L) are 2.1× and 1.4× the hand-placement repeat distance
for the same landmarks, so the rule is *close to* the hand reference
but not at the level of a second human placer. This is documented
honestly, not tuned away.

**Extending to case02 and case03.** Same rule, same parameter. The
only failure mode to watch:

- **`condyle_medial` and `condyle_lateral` too close (< 20 mm apart)**
  → the half-split landed between two parts of the same condyle, not
  between two distinct blobs. Visible when the femur's distal
  cross-section is not two-lobed at the 5 mm level (rare in normal
  anatomy; suspect a mask artefact).
- **Separation large but centre error > 12 mm** → the hand reference
  for that subject is again lateral-biased. Cross-check against the
  femur's slab centroid; if the hand click is more than ~5 mm off it,
  the hand reference is the suspect, not the code.

Both sides use the same rule; the medial/lateral labelling is
side-detected via `np.median(femur_verts[:, 0]) < 0` and asserted in
the test.

## Scope

Placed:
- case01: 14 landmarks (all 10 right-side plus 4 left-side surface
  landmarks) and a full repeat set

Pending:
- case02, case03: not yet placed (segmentations not yet merged;
  extension plan is "same landmarks, same rules, adjust medial window
  if needed")

Left-side joint-line landmarks (`condyle_*_L`, `plateau_*_L`) are
placed once without a repeat on case01 and are not used by the HKA/MAD
pipeline. They would be needed only if mLDFA/MPTA on the left leg is
attempted, which is out of scope for this sprint.
