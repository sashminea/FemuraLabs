# Landmark placement guide

Click-by-click instructions for placing the ten landmarks the pipeline
uses. Generated from annotated screenshots of case01 by Gemini, then
verified on case01 by placing each landmark multiple times and
measuring repeat distance (see `docs/CONVENTIONS.md`).

Use this guide to place landmarks on case02, case03, and any future
subject, so that placement is consistent across subjects. Wording is
plain on purpose; each step names what to look for in the image.

## Conventions used below

- **Primary view** — the 2D view to work in first. Chosen for each
  landmark because it makes the reference features most visible.
- **Secondary view** — the view that confirms placement.
- **"Safe cortical offset"** — place the point slightly inside the
  bone boundary, not on the very edge of the mask. Keeps the point
  inside the mesh after marching cubes, so distance and volume
  calculations do not see a point the mesh does not contain. 1–2
  voxels of inset is enough.
- **"Midpoint"** — arithmetic average of two clicked points. When a
  landmark is defined as a midpoint, click the two anchors first,
  then place the landmark at their average. This is why anchor-based
  landmarks reach 2 mm repeatability and surface-click landmarks sit
  at 7–9 mm.

## The 10 landmarks

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
- Placing at the neck-base junction, where the ball meets the
  shaft — visible in axial as a slice just below the largest
  circle.

### `femoral_head_L`

Same steps, left side. Mirror image of the scan.

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

### `knee_centre_L`

Same steps, left side.

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
- Floating in the joint gap — visible in coronal as a point
  suspended in the dark space above the talus.
- Off-centre anterior/posterior — visible in axial as a point at
  the front or back of the talus body rather than in its middle.

### `ankle_centre_L`

Same steps, left side.

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
- Floating above the joint line — visible in coronal as a point
  not touching the condyle surface.

**Anchor note:** this landmark is defined as "the intersection of
two surface directions". If it repeats badly, the fix is to click
the medial-most and lateral-most points on the condyle's joint-line
edge separately, then use their midpoint as the landmark. That
converts the surface click into a midpoint anchor.

### `condyle_lateral_R`

Same steps as `condyle_medial_R`, on the lateral (outer) side.
Faces away from the other leg.

### `plateau_medial_R`

**Primary view:** Coronal. **Secondary view:** Axial.

1. In coronal, scroll to the widest section of the knee joint.
2. Focus on the medial (inner) side of the right shin bone (blue
   mask), facing toward the other leg.
3. Find the highest (most proximal) point on the flat top rim of
   the medial tibial plateau, right against the joint line.
4. Find the innermost medial edge of this platform.
5. Click at the top-inner corner, with the safe cortical offset.

**Verification:** Axial — the point sits on the innermost boundary
of the upper right shin bone.

**Common mistakes:**
- Placed on the lateral plateau by mistake.
- Floating in the joint gap above the plateau.

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

### Left-side surface landmarks (`condyle_*_L`, `plateau_*_L`)

Same steps as the right side, mirror image. These are placed once
without a repeat and are not used by the HKA/MAD pipeline; they are
needed only if mLDFA/MPTA on the left leg is attempted.

## Note on the anchor-vs-guess distinction

Places where Gemini's instructions say "midpoint between A and B"
(ankle centres) or "intersection of two edges" (condyle and plateau
landmarks) are anchor-based. When actually placing, click the two
anchors first, note their coordinates, compute the midpoint, and
place the landmark there — do not eyeball the midpoint. That is the
difference between 2 mm and 16 mm repeat distance.