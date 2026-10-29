# Design decisions

Architectural choices that a reader might reasonably want to reverse.
Each entry: **Decision**, **Alternative rejected**, **Reason**,
**Consequence**. Entries are numbered from the original sequence; gaps are
entries pruned during a 27 October 2026 documentation cleanup. Only the
decisions still load-bearing for the current code are recorded.

New entries go at the top.

---

## D033: `knee_centre` uses the two-condyle split, not the whole-slab centroid

**Decision:** `knee_centre` takes the bottom 5 mm of the femur mesh,
splits that slab at its own x mid-point, takes each half's vertex
centroid (approximating the medial and lateral condyle blobs), and
returns their mean. The tibia is accepted in the signature but not used.
The return shape is `(centre, info)` where `info` carries
`condyle_medial`, `condyle_lateral`, `slab_mm`.

**Alternative rejected:** Keep the draft (average of the whole distal
femur cross-section centroid and the whole proximal tibia
cross-section centroid); or a tibia-only rule; or a curve-fit around
the condyle outline.

**Reason:** The draft was 10–14 mm off on case01. The diagnostic
printed dy = +10 mm on **every** variant (mesh vs mask, 5 mm vs 20 mm
slab), which ruled out vertex density and slab thickness as causes and
pointed at the tibia. Splitting femur-only vs tibia-only vs averaged
showed the tibia was the source of dy: the proximal tibia centroid is
~14 mm anterior of the distal femur centroid, and averaging pulls the
result posterior. The right-side x error of +9 to +12 mm on every
whole-slab variant came from the whole-cross-section centroid being
pulled toward the medial condyle (which is larger). Splitting at the
x mid-point and averaging the two halves is rule (a) from
`docs/conventions.md` taken literally — "midpoint between centres of
the medial and lateral condyle blobs" — and halves both errors
(14.00 → 6.36 mm on the right; 10.43 → 7.21 mm on the left).

**Consequence:** Signature changed from `-> np.ndarray` to
`-> tuple[np.ndarray, dict]`, mirroring `ankle_centre`. `tibia_verts`
is accepted but ignored; keeping it in the signature means a future
joint-line rule that needs both bones (mLDFA, MPTA — see D032's
"joint-line angles" note) does not have to re-plumb the call sites in
`pipeline_demo.py` and downstream code. The right-side residual of
6.36 mm is not a code defect: the hand click sits 8.7 mm lateral of
the femur slab's x-centroid, while the left-side hand click sits 0.4 mm
away — an asymmetry in the hand reference that no symmetric automated
rule can match. The 10 mm test threshold is generous on purpose, and
the diagnostic assertions (medial/lateral separation > 20 mm,
medial-vs-lateral ordering per side) fire **before** the tolerance so
a real regression never hides behind a loose error bound.

**Not resolved in D033:** the return shapes across the three rules are
now inconsistent. `femoral_head_centre` returns `(centre, radius, rms)`
because radius and rms are the diagnostic quantities for a sphere fit;
`ankle_centre` and `knee_centre` return `(centre, info_dict)` because
the diagnostics are the intermediate points, not scalar fit statistics.
A future unification could make all three return `(centre, dict)` with
`radius`/`rms` inside the dict for the head fit, but that would change
call sites in `tests/test_landmarks.py` and any downstream consumer for
no functional gain. Deferred.

---

## D032: extend `combined_seg.nii` from four to six labels (add fibula)

**Decision:** The merged segmentation now carries six labels:
femur_R=1, femur_L=2, tibia_R=3, tibia_L=4, **fibula_R=5, fibula_L=6**.
The two fibula labels are read from `shanks_on_full.nii` at source
values 3 (fibula_R) and 10 (fibula_L) and mapped to 5 and 6 by the
same merge script. No other bone was added. Talus is deliberately
absent (see Consequence).

**Alternative rejected:** Keep the merged file at four labels and
approximate the ankle centre from the tibia alone; or add all fifteen
source labels (talus, calcaneus, tarsals, metatarsals, phalanges) so
that future rules have everything on hand.

**Reason:** The ankle-centre rule in `docs/conventions.md` is rule
(a): "midpoint between the medial and lateral malleoli, projected to
the top of the talus." The lateral malleolus is part of the fibula,
not the tibia. On case01, a tibia-only version of the rule produced
an ankle-centre error of 22.4 mm (right) and 25.8 mm (left) against
the hand-placed reference — 10× the hand-placement repeat distance
and far larger than the medial-only bias the previous docstring
anticipated. Extending the merge with the fibula is what the
documented rule requires; the alternative was to change the rule to
one that contradicts `conventions.md`. Extending to all fifteen
source labels was rejected because each bone added is a naming
decision, a documentation line, and a set of tests that must
justify it. Only fibula has a documented use in the pipeline today.

**Consequence:** `masks.LABEL_NAMES` has six entries. `extract_masks`
returns `fibula_R` and `fibula_L` alongside the four existing bones;
any caller that iterates `masks.values()` now gets six items, so a
caller that assumed four must filter by name. `pipeline_demo.py`
writes two extra STL files and two extra `bones` entries in
`summary.json` — this is desired (the fibula is part of the deliverable
for a lower-limb analysis) but changes the output shape of D05. The
existing tests pass unmodified because they iterate the dict rather
than hard-code four. **Talus remains absent** even though rule (a)
cites the top of the talus: on case01 the tibia centroid at the
plafond level lands within 3 mm of the hand click in y, so the
plafond is a usable proxy for the talar dome directly beneath it. The
residual 3 mm is noted in `docs/landmarks.md` (ankle_centre,
"Why no talus yet") as the trigger for adding talus if a future
subject exceeds 3 mm of y error. This is a deliberate scope cut, not
a forgotten bone.


---

## D031: femoral head fit constrained to a medial window

**Decision:** `femoral_head_centre` takes the top 25 percent of the femur
by z, then keeps only vertices within `medial_window_mm` (default 20 mm)
of the medial-most x. A linear sphere fit is applied to that region with
iterative outlier trimming.

**Alternative rejected:** Fit the whole proximal femur, or use a fixed
z-region without medial constraint, or use a curvature-based region
growing algorithm.

**Reason:** A fit to the whole proximal femur captures head, neck and
greater trochanter as one shape, giving a fit radius of 30–37 mm
(physiologically implausible for an adult femoral head) and a centre
that lands between the head and the trochanter. On case01, this produces
errors of 20–35 mm against the hand-placed reference. Constraining to
the medial window captures the medial hemisphere of the head, which is
enough to fix the sphere centre, and gives errors of 3.8 and 4.8 mm on
the two sides. The radius check (17–25 mm range) is what catches the
fit drifting onto the trochanter.

**Consequence:** The default `medial_window_mm=20` is a starting point
that works for typical adult femoral heads. For subjects with unusually
small or large heads, the correct window must be found by the diagnostic
sweep described in `docs/landmarks.md`. A future iteration could
automate that sweep: try windows in ascending order and take the first
one that returns a radius in the anatomical range. That is not done in
D08 because a single-subject reference cannot validate the automatic
window selection.


## D030: `load_landmarks` respects the file's coordinate-system field

**Decision:** `load_landmarks(path)` reads each markup's
`coordinateSystem` field and negates x and y only when the field is
`"RAS"`. Files declaring `"LPS"` (Slicer 5.x default) are returned
unchanged. Unset field is treated as LPS.

**Alternative rejected:** Assume all Slicer files are RAS and always
negate x and y.

**Reason:** Slicer 5.12 saves `.mrk.json` with
`"coordinateSystem": "LPS"`. The pipeline's first pass double-negated
x and y (once from the loader, once from the file's LPS interpretation),
which put every femoral head on the posterior side of the body — visible
as a 290 mm error between the loaded landmark and the mask centroid, but
silent to any code that did not have a reference to compare against. The
fix is to trust the file's declared coordinate system, not to assume one.

**Consequence:** A RAS-declaring Slicer file (older Slicer versions, or
files converted from another tool) will still be handled correctly.
A future decision that changes the pipeline to RAS would need to invert
the branch but not the field reading.


## D029: label sides by anatomy, not by screen position

**Decision:** In all landmark files, `_R` suffixes mean the patient's
right side, which appears on the **left** of Slicer's default axial view
(radiological convention, viewed from the feet). The landmark placement
guide in `docs/landmark_placement.md` states this explicitly and
instructions for each `_R` landmark say "check the axial view's corner
labels".

**Alternative rejected:** Label by screen position ("the one on the
right of the screen").

**Reason:** The first placement session on case01 labeled screen-right
as `_R`, which gave femoral head positions of +94 mm LPS x for `_R`
(wrong: that is the patient's left) and −71 mm for `_L` (wrong: that is
the patient's right). The error was not caught by any test until a
comparison against the mask centroid, which has the correct sign. The
fix requires the convention to be stated everywhere a landmark is
described.

**Consequence:** Any future landmark file must have `_R` landmarks on the
negative-x side (LPS) and `_L` landmarks on the positive-x side. A
future test that asserts this on the loaded `femoral_head_R` and
`femoral_head_L` would catch the swap before it reaches downstream
computation. The current test suite does not assert this directly; it is
caught indirectly because a swap produces a 300 mm error against the
mask centroid in `test_femoral_head_right_agrees_with_hand_placement`.
A direct assertion is worth adding in Sprint for landmarking.

---

## D028: `is_watertight` tolerates a small fraction of non-manifold edges

**Decision:** `is_watertight(verts, faces, tol=0.001)` returns True if the
mesh has zero boundary edges (count-1 edges) and non-manifold edges
(count-3+ edges) are fewer than 0.1 percent of total faces.

**Alternative rejected:** Exact check — every edge shared by exactly two
faces.

**Reason:** skimage's marching cubes with `allow_degenerate=True` (the
default) produces a handful of non-manifold edges where two surface
patches touch at an edge. On case01's right femur: 0 boundary edges,
6 non-manifold edges, 560,642 faces — 0.0007 percent. Exact count-2
would fail this mesh even though it is closed and volume-computable,
and removing the degenerate triangles (via `allow_degenerate=False`)
opens the mesh elsewhere. The realistic property is closure plus
negligible non-manifoldness, not exactness.

**Consequence:** `edge_incidence(verts, faces)` returns the three counts
(boundary, manifold, non-manifold) and is exposed for diagnostics. The
boolean wrapper is a convenience. A test that asserts `boundary == 0` and
`non_manifold / faces < 0.001` is the correct assertion for a real mesh;
asserting `counts["manifold"] == len(edges)` is not.


## D027: `mask_to_mesh` keeps degenerate triangles

**Decision:** `mask_to_mesh` calls `measure.marching_cubes` with the
default `allow_degenerate=True`.

**Alternative rejected:** `allow_degenerate=False`, which removes
zero-area triangles produced where two surface patches meet at an edge.

**Reason:** Zero-area triangles contribute no volume or area, but they do
contribute topology: they keep the surface closed at every edge. Removing
them opens the mesh at the exact points where two patches touch. On
case01's right femur, `allow_degenerate=False` produced a mesh with
non-zero boundary edges (open) and `allow_degenerate=True` produced a
closed mesh with 6 non-manifold edges out of 840,957. Closed with 0.0007
percent non-manifold is preferred over open.

**Consequence:** Downstream code that computes volume, area, or boolean
operations must tolerate the presence of degenerate triangles. `signed_volume`
and `edge_incidence` in `mesh.py` do. If a future operation cannot, it
must filter them explicitly and document why.


## D026: `io_volume.Volume` has array in (z, y, x), geometry in (x, y, z)

**Decision:** The `Volume` dataclass returned by `load_volume` has
`array` in numpy's (z, y, x) order (matching `GetArrayFromImage`), while
`spacing`, `origin` and `direction` are in SimpleITK's (x, y, z) order
(matching `GetSpacing`, `GetOrigin`, `GetDirection`). The dataclass is
the contract: any function that converts between array and world
coordinates must reorder the array indices.

**Alternative rejected:** Return the array in (x, y, z) order by
transposing, so that array and geometry share one axis order.

**Reason:** SimpleITK's API returns these two forms; converting at the
boundary would either (a) slow every call with a transpose of a
512 × 512 × 1637 array (about 400 MB per copy) or (b) require calling code
to know whether the transpose has been applied. Keeping both in the
order SimpleITK gives them makes the contract one sentence long
("array is (z, y, x); geometry is (x, y, z)") and every downstream
function is responsible for the reorder once. The reorder is a
`verts[:, ::-1]` in `mask_to_mesh` and a `[x_i, y_i, z_i]` assignment in
`masks.extract_masks` — one line each, tested.

**Consequence:** `tests/test_io_volume.py::test_real_file_array_shape`
pins the contract by asserting `array.shape == (1637, 512, 512)` for a
file whose `GetSize()` is `(512, 512, 1637)`. Any future "fix" that
transposes the array will fail this test. The world-coordinate conversions
in `masks.py` and `mesh.py` both go through the same affine
(`origin + direction @ (spacing * index)`); if the axis order gets
swapped anywhere, the affected test fails.

## D025: combine the two reference segmentations into one multi-label NIfTI

**Decision:** Femur and tibia masks come from one multi-label NIfTI produced
in Slicer, on the `_1` grid, with labels femur_R=1, femur_L=2,
tibia_R=3, tibia_L=4.
in Slicer, on the `_1` grid, with labels femur=1, tibia=2, fibula=3. The two
source `.seg` files stay in `data/raw/` as the original record but are not
read by pipeline code.

**Alternative rejected:** Read the two `.seg` files directly in Python.

**Reason:** `.seg` is Slicer-internal; reading it from Python requires either
Slicer's interpreter or a NIfTI round-trip that the combined export does
anyway. Two grids downstream invite a silent mismatch.

**Consequence:** Any second subject uses the same combined-export step.
Licences and citations are in `CITATION.cff`; coverage is in `docs/data.md`.
**See also:** D032 extends the merged file from four to six labels
(fibula_R=5, fibula_L=6) for the ankle-centre rule.


## D022: `verdict` handles lower-is-better metrics by argument order

**Decision:** `verdict(base, cand, threshold)` treats the first list as
baseline, the second as candidate; higher is better. Lower-is-better metrics
are handled by swapping the arguments at the call site
(`verdict(cand_hd95, base_hd95, 1.0)`), not by a `direction` parameter.

**Alternative rejected:** A `direction: "increase" | "decrease"` parameter,
with internal sign flipping.

**Reason:** A direction parameter adds a branch and a place where a typo
silently produces a wrong verdict. Argument order puts the direction in the
caller's hands, where the semantics are visible.

**Consequence:** Callers with lower-is-better metrics must remember to swap.
The runbook records the convention. A guard uses a negative threshold:
`verdict(base, cand, -0.005)` asks "at most 0.005 worse".


## D016: mounts use `/data` (read-only) and `/output` (writable)

**Decision:** Containers that read host data mount it at `/data` with `:ro`;
containers that write results mount at `/output` with the default writable
mode. The image's `WORKDIR` is `/app`, and no mount overlaps anything under
it.

**Alternative rejected:** (a) A single `-v "$(pwd):/work"` mount, exposing
the whole repository. (b) `:rw` for the data mount. (c) Mounts inside `/app`.

**Reason:** (a) exposes `.git`, `runs/` and any future secrets file to the
container, defeating `.dockerignore`. (b) lets a bug modify or delete a scan.
(c) hides whatever the image holds at that path: mounting at `/app/src`
makes `femuralabs` invisible and every command fails with
`No module named 'femuralabs'`. The chosen paths are empty in the image, so
mounting there removes nothing.

**Consequence:** The CLI's `--file` and `--out` arguments name container paths
(`/data/volume.npy`, `/output`), not host paths. The output folder must be
created before the run as the host user; Docker creates missing bind-mount
folders as root, and the container's `student` (UID 1000) cannot write to
them.


## D014: extract `save_json` to `toolkit/io.py`; `save_config` and `write_info` share it

**Decision:** The primitive — create parent folders, `json.dumps`, write,
append a trailing newline — lives once in `femuralabs.toolkit.io.save_json`.
`training/train_utils.save_config` and `toolkit/report.write_info` both call
it.

**Alternative rejected:** (a) Reimplement the two-line body in `write_info`.
(b) Import `save_config` from `train_utils`.

**Reason:** (a) is a second definition of the same operation, which drifts.
(b) fails inside the tool container: `train_utils` imports `torch`, and the
tool image ships numpy only (D001, D011). Extracting to a module that does
not pull `torch` lets both callers share the primitive and keeps it in the
image.

**Consequence:** `save_config` becomes a one-line wrapper. `write_info` writes
`out_dir/info.json` in one line. Two public functions, one implementation.


## D011: image runs as non-root `student`; `training/` excluded

**Decision:** The `Dockerfile` creates the account `student` (UID 1000) before
`COPY src/`, then switches to it with `USER student`. The `training/`
subpackage is excluded from the build context by `.dockerignore`.

**Alternative rejected:** Run as root (the base image default) and ship all
of `src/`.

**Reason:** A container runs as root on the host kernel; one kernel exploit
turns "container compromised" into "host compromised". Nothing this project
does needs root. `training/` imports `torch`, which the tool image does not
install (D001), so shipping it adds dead code that cannot even be imported.

**Consequence:** Any file the container writes must be writable by UID 1000.
A bind-mounted output folder created by root on the host is unwritable by the
container; create it with the host user before running.


## D010: `training/` and `service/` subpackages; singletons stay flat

**Decision:** `model.py` and `train_utils.py` live under
`femuralabs.toolkit.training`; `routes.py`, `api.py` and `serve.py` live
under `femuralabs.toolkit.service`. `arrays.py`, `summary.py`,
`volume_info.py`, `cli.py`, `io.py`, `report.py` and `decision.py` stay flat.

**Alternative rejected:** Group everything by domain (`image/`, `geometry/`,
`io/`) in one refactor.

**Reason:** A folder with one file adds a path segment to every import and
every `python -m` command without grouping anything. The two groups created
here have two or more files each, share one purpose, and are expected to
grow. Singletons grow into a folder when their second file arrives.

**Rule adopted:** a subpackage appears when two or more files share one
purpose and are expected to grow. Singletons stay flat.

**Consequence:** `python -m femuralabs.toolkit.service.serve` replaces the
old import path. The `Dockerfile` copies `src/` wholesale, unaffected.


## D001: `requirements-tool.txt` separate from `requirements.txt`

**Decision:** The tool container installs from `requirements-tool.txt` (one
pinned numpy line). The development environment installs from root
`requirements.txt`, which pulls PyTorch from the CUDA wheel index.

**Alternative rejected:** One requirements file for all environments.

**Reason:** `requirements.txt` installs PyTorch from the CUDA wheel index,
which is several gigabytes. The tool container executes numpy only — no
training, no GPU, no CUDA. Shipping PyTorch into the tool image multiplies
its size by roughly two orders of magnitude and makes every `docker pull`
impractical.

**Consequence:** Two files must stay in sync when numpy's pinned version
changes. The `Dockerfile` copies `requirements-tool.txt`, not
`requirements.txt`.