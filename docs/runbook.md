# Runbook

This document walks through the entire FemuraLabs pipeline, from environment setup to validation reports. Sections are ordered by the sequence you'd actually follow them in. If you're new to the repo, start at "Quick start".

Every command here was run on the development workstation (WSL2 Ubuntu, 7.7 GB RAM, no GPU) and its output was captured. GUI procedures describe exactly what was clicked. Where you see "Expected:" followed by a block, that is the actual output — diff against yours to catch a silent error.

---

## Quick start

If you just want to confirm the repo works, run these three commands. They take ~2 minutes total and require no data.

```bash
cd ~/FemuraLabs
source .venv/bin/activate
pytest -q                          # 62 tests, all passing
docker build -t femuralabs-tool .  # ~2 min, downloads ~1.2 GB
docker run --rm femuralabs-tool    # runs the pipeline on a synthetic volume
```

If all three succeed, the code, dependencies, and container are working. Everything below is about real data.

---

## 1. Environment setup

Run this before any other command in a new terminal. Three checks: are you in the right folder, is the venv active, are unexpected files modified.

```bash
cd ~/FemuraLabs
source .venv/bin/activate
pwd
which python
git status
```

Expected:
- `pwd` ends in `FemuraLabs`.
- `which python` contains `.venv`.
- `git status` reports either `nothing to commit` or only files intended for change.

If `pwd` is wrong, later commands fail for unrelated reasons (e.g., `pytest` collects nothing, `docker build .` copies the wrong context). If `which python` does not contain `.venv`, pip installs into system Python instead of the project one.

On Windows the activation command is `.venv\Scripts\Activate.ps1`.

---

## 2. Running the test suite

The 62-test suite covers the array helpers, geometry primitives, mesh algorithms, landmark rules, alignment math, statistical functions, metrics, I/O, the CLI, the report writer, and the HTTP service. It runs in ~2 minutes and is the cheapest check that nothing regressed.

```bash
pytest -q
```

Expected: a line ending with `passed`, no `failed`. `conftest.py` at the project root puts `src/` on the import path, so no `PYTHONPATH` prefix is needed.

If a test fails, the output names the file and line. **Do not change the test to match the code** — change the code, or add an entry to `docs/decisions.md` explaining why the expected value was wrong. The tests are written against hand-verifiable values (e.g., a straight synthetic limb gives HKA = 0° exactly), so a test failure means the code drifted.

**Disk space on WSL2:** `pytest` writes ~200 MB of temporary files per run. To prevent the WSL virtual disk from growing without bound, `pytest.ini` redirects `tmp_path` to `/dev/shm/pytest_tmp` (a RAM disk), and `conftest.py` wipes it after every run. If you ever see the C: drive filling up, that is a WSL2 virtual-disk issue, not a pytest issue — see `docs/decisions.md` D042.

---

## 3. Data preparation

The Zenodo dataset (record 8302449, `VSDFullBodyBoneReconstruction`) ships in **three different layouts**. You need to identify which layout a subject uses before doing anything else.

| Layout | What's in the zip | How we handle it |
|---|---|---|
| **A. Standard lower-limb** | One `SMIR.Lower_limb...nrrd`, four `.seg.nrrd` | Slicer export → `merge_segmentation.py` |
| **B. Full-body upside-down** | One `SMIR.Body...nii`, four `.seg.nrrd`, `Transform-Upside-Down.h5`, `.mrml` | `process_full_body_raw.py` (pure Python) |
| **C. Split volume, mixed patients** | Two separate CT volumes, sometimes from different patients | **Discard this subject.** Cannot be salvaged |

The full list of subjects used, with their layouts, is in `docs/data.md` under "Subject-to-Case Mapping".

### 3.1 Identify the subject's layout

```bash
python scripts/dev/inventory_dataset.py --dir /mnt/d/Femuralabs/D07 --filter zXXX
```

Replace `zXXX` with the zip number (e.g., `z061`, `z062`, `z064`, `z066`). The script recurses any depth and prints absolute paths categorized by file type. If it lists a `SMIR.Body...nii` plus a `.h5` transform, the subject is Layout B. If it lists a `SMIR.Lower_limb...nrrd`, it's Layout A.

**Before running the inventory**, download the zip and unzip it (approximately 1–2 GB per subject, all on the `D:` drive to preserve C: space):

```bash
zenodo_get 8302449 -g "zXXX.zip" -o /mnt/d/Femuralabs/D07/temp_zips
cd /mnt/d/Femuralabs/D07/temp_zips && unzip zXXX.zip
```

### 3.2 Layout A: Standard lower-limb (e.g., case01, case02, case03)

These subjects ship with a clean full-limb CT (`SMIR.Lower_limb...nrrd`) and two segmentations. The workflow is Slicer export → merge.

**Producing the thighs NIfTI:**

1. In 3D Slicer, `File → Add Data`, open the `SMIR.Lower_limb...nrrd`.
2. Confirm in `Modules → Volumes → Volume Information` that dimensions are ~512 × 512 × 1500+.
3. `File → Add Data`, open the `-Pelvis-Thighs_Reconstruction.seg.nrrd`.
4. **`Modules → Segment Editor`** — not Segmentations. Set the **Source Volume** dropdown to the full-limb CT.
5. Click the small icon to the right of Source Volume (the **Segment Geometry** dialog). Confirm dimensions match the CT (~512 × 512 × 1637). Click **OK**. This step is mandatory — without it the export is crop-sized.
6. **`Modules → Segmentations`** — not Segment Editor. Scroll to **"Export to files"**, set format `NIFTI (.nii)`, choose a `D:` destination folder, click **Export**.
7. Copy the `.nii` and `.labels.csv` to WSL under a fixed name:

```bash
cp /mnt/d/Femuralabs/D07/exports/caseXX/*Pelvis-Thighs_Reconstruction.nii data/raw/caseXX/thighs_on_full.nii
cp /mnt/d/Femuralabs/D07/exports/caseXX/*Pelvis-Thighs_Reconstruction.labels.csv data/raw/caseXX/thighs_on_full.labels.csv
```

**Producing the shanks NIfTI:** repeat steps 3–7 with `-Shanks-Feet_Segmentation.seg.nrrd` (Segmentation, not Reconstruction), saving as `shanks_on_full.nii` / `shanks_on_full.labels.csv`.

**Verify both files are on the same grid:**

```bash
python -c "
import SimpleITK as sitk
a = sitk.ReadImage('data/raw/caseXX/thighs_on_full.nii')
b = sitk.ReadImage('data/raw/caseXX/shanks_on_full.nii')
print('thighs:', a.GetSize(), a.GetSpacing())
print('shanks:', b.GetSize(), b.GetSpacing())
"
```

Both must print identical sizes and spacings. If either is crop-sized (`(312, 205, 889)` or similar), the Segment Geometry step was skipped — go back to step 5 for that file.

**Merge into one multi-label file:**

```bash
PYTHONPATH=src python scripts/data/merge_segmentation.py \
  --thighs data/raw/caseXX/thighs_on_full.nii \
  --shanks data/raw/caseXX/shanks_on_full.nii \
  --out    data/raw/caseXX/combined_seg.nii
```

The script reads each subject's `.labels.csv` to look up source label values by name (e.g., `Femur_R` → some integer that varies per subject), so it does not assume case01's numbers. It prints each mapping with voxel counts. Expect `Femur_R ~500,000` voxels, `Tibia_R ~300,000`, `Fibula_R ~77,000`. A zero means the CSV was wrong or the export was crop-sized.

**Clean up the intermediates** to save space:

```bash
rm data/raw/caseXX/thighs_on_full.* data/raw/caseXX/shanks_on_full.*
```

### 3.3 Layout B: Full-body upside-down (e.g., case04–case08)

These subjects ship a full-body CT (`SMIR.Body...nii`), separate segmentations, and a `Transform-Upside-Down.h5` file. The raw CT is stored feet-first, so the array is upside down. **Do not use Slicer to export these** — Slicer drops the H5 translation when exporting and the geometry breaks.

Instead, one Python script does everything: it reads the H5 transform, extracts the raw leg bounding box from the CT (bypassing OOM), combines the segmentations, and centers the patient at X=0.

```bash
PYTHONPATH=src python scripts/data/process_full_body_raw.py \
  --ct /mnt/d/Femuralabs/D07/temp_zips/zXXX/zXXX/SMIR.Body...nii \
  --thighs-seg /mnt/d/Femuralabs/D07/temp_zips/zXXX/zXXX/...Pelvis-Thighs_Reconstruction.seg.nrrd \
  --shanks-seg /mnt/d/Femuralabs/D07/temp_zips/zXXX/zXXX/...Shanks-Feet_Segmentation.seg.nrrd \
  --transform /mnt/d/Femuralabs/D07/temp_zips/zXXX/zXXX/Transform-Upside-Down.h5 \
  --out-dir data/raw/caseXX
```

Expected output on `case04`:

```text
Mapped Femur_R from thighs (idx 1) -> 1 (354465 voxels)
Mapped Femur_L from thighs (idx 2) -> 2 (347109 voxels)
Mapped Tibia_R from shanks (idx 1) -> 3 (48372 voxels)
...
Final size: (276, 170, 2459)
```

**Read the log:** each `Mapped` line names the source label value the script found in the CSV (varies per subject), the destination label (fixed by D032), and the voxel count. A zero for `Talus_R` or `Talus_L` means the source data did not annotate that bone — this is common in VSD and the pipeline tolerates it.

### 3.4 Verifying any prepared subject

Whichever layout you used, the output is `data/raw/caseXX/combined_seg.nii` with 8 labels (0 = background, 1–8 = the six main bones plus two talus). Run the standard check:

```bash
PYTHONPATH=src python -c "
from femuralabs.toolkit.fileio.volume import load_volume
from femuralabs.toolkit.imaging.masks import extract_masks
v = load_volume('data/raw/caseXX/combined_seg.nii')
m = extract_masks(v)
print('femur_L x:', m['femur_L'].centroid_world[0])
print('femur_R x:', m['femur_R'].centroid_world[0])
"
```

Expected: `femur_L x` positive, `femur_R x` negative, both roughly symmetric (±90 to ±115 mm depending on subject size). This is the single most important check — if the sides are swapped, every downstream angle is wrong.

**Diagnostic if sides are wrong:**
- Both positive, or both negative: the centering step failed. Re-run `process_full_body_raw.py` (Layout B) or investigate the direction matrix (Layout A).
- Only one side wrong: the mask files were mixed up during merge (e.g., `thighs_on_full` was from a different subject). Check with `git status` that no temporary files crossed between case folders.

**Additional check — the mask sits on the bone.** Load `data/raw/caseXX/combined_seg.nii` and `data/raw/caseXX/ct_cropped.nii` (Layout B) into Slicer, set opacity to 0.4, scroll to the knee. The colored mask must sit exactly on the CT bone. If they are offset, the geometry is broken.

---

## 4. Landmark placement

Every subject needs 10 hand-placed landmarks. This is the human reference that later stages compare the automatic rules against. It takes 30–60 minutes per subject.

**Setup in Slicer:**

1. Open Slicer.
2. `File → Add Data`, load `data/raw/caseXX/ct_cropped.nii` (Layout B) or the full-limb `.nrrd` (Layout A).
3. `File → Add Data`, load `data/raw/caseXX/combined_seg.nii` as a **Label Map**.
4. Right-click the label map in the Data module → **"Convert label map to segmentation node"**.
5. In `Modules → Segmentations → Display`, set opacity to 0.4.
6. Verify the colored mask overlays the CT bone in the axial, coronal, and sagittal views.
7. `Ctrl+Shift+F` to create a Markups node. Rename it to `landmarks_caseXX`.

**Place the ten landmarks** following `docs/landmarks.md`. In summary:

| Landmark | Placement |
|---|---|
| `femoral_head_R` / `_L` | Axial slice with the largest circular cross-section of the femoral head; center of that circle |
| `knee_centre_R` / `_L` | Axial at joint line, center of the intercondylar notch |
| `ankle_centre_R` / `_L` | Coronal at talar dome, midpoint of the two malleoli projected up |
| `condyle_medial_R` | Coronal at joint line, most distal-medial point of medial femoral condyle |
| `condyle_lateral_R` | Coronal at joint line, most distal-lateral point of lateral femoral condyle |
| `plateau_medial_R` | Coronal at joint line, most proximal-medial point of medial tibial plateau |
| `plateau_lateral_R` | Coronal at joint line, most proximal-lateral point of lateral tibial plateau |

**Two traps:**
- **Slicer's axial view is radiological.** Patient-right appears on screen-left. `_R` landmarks must be on the screen-LEFT side in axial.
- **The pipeline uses LPS millimetres.** `load_landmarks` reads the file's `coordinateSystem` field and only negates if it says `"RAS"`. Slicer 5.x writes `"LPS"` by default. Do not manually negate.

**Save:** `File → Save`. Save as `landmarks_caseXX.mrk.json` in `data/ref/`.

**Verify:**

```bash
PYTHONPATH=src python -c "
import numpy as np
from femuralabs.toolkit.fileio.landmark import load_landmarks
from femuralabs.toolkit.fileio.volume import load_volume
from femuralabs.toolkit.imaging.masks import extract_masks
h = load_landmarks('data/ref/landmarks_caseXX.mrk.json')
v = load_volume('data/raw/caseXX/combined_seg.nii')
m = extract_masks(v)
D = np.array(v.direction).reshape(3,3); S = np.array(v.spacing); O = np.array(v.origin)
def min_dist(pt, mask):
    zi, yi, xi = np.where(mask)
    xyz = np.stack([xi, yi, zi], axis=1)
    return float(np.linalg.norm(O + (xyz * S) @ D.T - pt, axis=1).min())
for name, bone in [
    ('femoral_head_R', 'femur_R'), ('femoral_head_L', 'femur_L'),
    ('knee_centre_R', 'femur_R'), ('knee_centre_L', 'femur_L'),
    ('ankle_centre_R', 'tibia_R'), ('ankle_centre_L', 'tibia_L'),
    ('condyle_medial_R', 'femur_R'), ('condyle_lateral_R', 'femur_R'),
    ('plateau_medial_R', 'tibia_R'), ('plateau_lateral_R', 'tibia_R'),
]:
    if name not in h: continue
    x = h[name][0]
    side_ok = 'OK' if (('_R' in name and x < 0) or ('_L' in name and x > 0)) else 'WRONG SIDE'
    print(f'{name:<20} x={x:>7.1f} {side_ok:<10} dist={min_dist(np.array(h[name]), m[bone].mask):.2f} mm')
"
```

Expected: every `side_ok` is `OK`, every `dist` is under 3 mm (knee_centre will be ~2.5 mm because it sits in the joint gap, not on bone).

---

## 5. Running the geometric pipeline

The pipeline takes `combined_seg.nii` plus optional landmarks and produces a `summary.json` with mesh statistics, volumes, and alignment angles. It runs in 20–60 seconds per case.

### 5.1 Single case

```bash
PYTHONPATH=src python scripts/pipeline/pipeline_demo.py \
  --case data/raw/caseXX/combined_seg.nii \
  --out output/caseXX \
  --compare data/ref/landmarks_caseXX.mrk.json \
  --angles
```

Expected output on any case:

```text
Loading volume: data/raw/caseXX/combined_seg.nii
  Extracting and meshing: femur_R...
  Extracting and meshing: femur_L...
  ... (eight bones)
  Comparing against: data/ref/landmarks_caseXX.mrk.json
  Computing angles...
Wrote output/caseXX/summary.json
```

The `--compare` and `--angles` flags are optional. Without them, only mesh stats and volumes are computed. With them, the summary also contains `landmarks` (auto vs hand error per landmark) and `angles` (HKA, MAD, mLDFA, MPTA per side).

**Memory note:** the pipeline processes one bone at a time and calls `gc.collect()` between, keeping peak memory at ~3 GB even on the largest subject. This is a D038 decision; do not "optimize" it back to loading all masks at once.

### 5.2 All cases

Once every subject under `data/raw/` has a `combined_seg.nii` and a `landmarks_caseXX.mrk.json`, run:

```bash
PYTHONPATH=src python scripts/pipeline/run_all_cases.py
```

The script iterates `CASES = ["case01", ..., "case08"]` (edit this list if you have more or fewer). It calls `pipeline_demo.py` with `--compare` and `--angles` for each case, writing `output/caseXX/summary.json`.

---

## 6. Generating reports

The reports are generated from the JSON summaries, never hand-typed. This is a D039 decision: manual transcription eventually drifts from the data.

```bash
python scripts/pipeline/make_report_tables.py
```

Writes:
- `reports/landmark_errors.md` — per-case, per-landmark error table with means
- `reports/angles_case.md` — HKA / mLDFA / MPTA comparison with bias and limits of agreement
- `reports/segmentation_errors.md` — Dice and HD95 per case per bone (requires `reports/seg_results_caseXX.json` from TotalSegmentator, see §7)

**Rule:** after any pipeline run that changes a `summary.json`, re-run this script. Do not edit the markdown files by hand.

---

## 7. Second method: TotalSegmentator

We compare the human reference masks against TotalSegmentator v2.18.0, a pretrained nnU-Net model. This section documents the run on limited hardware (7.7 GB usable RAM); on a machine with 32+ GB RAM you can skip most of it.

### 7.1 Installation

```bash
pip install TotalSegmentator
totalseg_set_license -l <academic_license_number>
```

The license is free for academic use. Never commit it — `git grep` must return nothing for the number.

### 7.2 The RAM trap

TotalSegmentator's prediction step is memory-light (it slides a window over the volume), but the final **resampling step** allocates a tensor for all 117 classes at full resolution. On a 512×512×1637 CT, that allocation is roughly 200 GB. On 7.7 GB RAM the OS kills the process with `SIGKILL: 9`.

**What we tried and what failed:**
- `--fast`, `--fastest`: still OOM at resample.
- `--force_split`, `--body_seg`: split the prediction, but resample still spikes.
- `--nr_thr_saving 1`: helps the save step, not the resample.

**The working solution:** run TotalSegmentator on a tightly cropped CT, then paste the mask back. See §7.3.

### 7.3 Running on limited RAM

The wrapper script handles everything:

```bash
PYTHONPATH=src python scripts/data/run_totalseg_all.py
```

For each case in `CASES = ["case01", "case02", "case03"]`, it:
1. Crops the CT to the reference mask bounding box (using `combined_seg.nii`).
2. Runs TotalSegmentator on the small crop.
3. Waits for the OOM-killed parent to be replaced by the detached child, which saves the mask to disk.
4. Pastes the cropped mask back onto the full 512×512×1637 grid.

If you want to run a single case manually:

```bash
PYTHONPATH=src python scripts/data/totalseg_bbox_crop.py \
  --ct data/raw/caseXX/caseXX_ct.nii.gz \
  --ref data/raw/caseXX/combined_seg.nii \
  --out output/totalseg/caseXX \
  --task total
# If killed, then:
python scripts/data/paste_back.py \
  --seg output/totalseg/caseXX/totalseg_cropped.nii \
  --ref-ct data/raw/caseXX/caseXX_ct.nii.gz \
  --out output/totalseg/caseXX/segmentation_full.nii.gz
```

### 7.4 Comparing segmentations

Once both tasks (`total` for femurs, `appendicular_bones` for tibias/fibulas) have produced full-size masks:

```bash
PYTHONPATH=src python scripts/pipeline/compare_segmentations.py \
  --ref data/raw/caseXX/combined_seg.nii \
  --ts-total output/totalseg/caseXX/segmentation_femurs.nii.gz \
  --ts-app output/totalseg/caseXX_appendicular/segmentation_full.nii.gz \
  --out reports/seg_results_caseXX.json
```

The script maps TotalSegmentator's label IDs to bone names dynamically (v2.18.0 uses 75/76 for femurs, 2/3 for tibia/fibula which must be split at the midline — see D041). It prints a Dice/HD95 table.

**Expected on case01:**

```text
femur_R    | 0.709  |     6.92
femur_L    | 0.674  |     6.54
tibia_R    | 0.670  |     5.90
tibia_L    | 0.632  |     5.12
fibula_R   | 0.739  |     2.80
fibula_L   | 0.724  |     2.80
```

The 3 mm downsampling means Dice caps around 0.75 on this cohort; native resolution runs would push it higher. This is documented as a limitation in `reports/validation.md`.

---

## 8. Docker container

The container packages the geometry pipeline and runs it on a synthetic 8-bone volume, so anyone can verify the build without downloading real data.

### 8.1 Build

```bash
docker build -t femuralabs-tool .
```

~2 minutes on first build (downloads scipy etc.), seconds on rebuild. Installs numpy, SimpleITK, scikit-image, scipy — **not** PyTorch or TotalSegmentator.

### 8.2 Run

```bash
docker run --rm femuralabs-tool
```

Expected:

```text
Generated synthetic case at /tmp/synthetic_case/combined_seg.nii
Running pipeline...
Loading volume: /tmp/synthetic_case/combined_seg.nii
  Extracting and meshing: femur_R...
  ... (eight bones)
Wrote /tmp/output/summary.json
```

The container runs as `student` (UID 1000, non-root). All files are in `/tmp`, nothing is written to the host.

### 8.3 Mount real data read-only

To run against a real subject without baking it into the image:

```bash
mkdir -p output
docker run --rm \
  -v "$(pwd)/data:/data:ro" \
  -v "$(pwd)/output:/output" \
  femuralabs-tool \
  python scripts/pipeline/pipeline_demo.py \
    --case /data/raw/case01/combined_seg.nii \
    --out /output/case01
```

`/data` is read-only (enforced by Docker), `/output` is writable. Create `output/` on the host **as your user** before running — Docker creates missing mount folders as root, which the container's `student` user cannot write to.

---

## 9. HTTP service and Compose

The repo ships a small HTTP service that serves `/health` and `/info`. It is not used by the geometric pipeline but is included as a demonstration of a deployment target.

### 9.1 Run standalone

```bash
PYTHONPATH=src python -m femuralabs.toolkit.service.serve
# In a second terminal:
curl http://localhost:8000/health
curl http://localhost:8000/info
```

Expected:

```text
{"status": "ok"}
{"shape": [4, 6, 6], "spacing": [2.0, 1.0, 1.0], "dtype": "float32", "extent_mm": [8.0, 6.0, 6.0]}
```

The bind address must be `0.0.0.0` (so Docker-published ports can reach it). `127.0.0.1` will refuse connections from the host.

### 9.2 Compose stack

`docker-compose.yml` runs `api` (built from the Dockerfile) and `web` (a static `http.server`) on a shared network.

```bash
mkdir -p output web
docker compose up --build -d
docker compose ps                                    # both running
curl http://localhost:8000/health                    # api on 8000
curl -I http://localhost:8080/                       # web on 8080
docker compose exec web python -c "import urllib.request; print(urllib.request.urlopen('http://api:8000/health').read())"
docker compose down
```

The `exec` test proves the two services resolve each other by name (`http://api:8000`) — the names only work on the private network.

**Failure modes:**
- `no configuration file provided`: you're not in the folder with `docker-compose.yml`.
- `port is already allocated`: another process holds 8000 or 8080. `docker compose ps` shows leftovers.
- `Permission denied` writing to `/output`: the host folder is owned by root. `rm -rf output && mkdir -p output`.

---

## Appendix A: Diagnostic scripts

Use these any time you suspect a subject is broken, before touching the main pipeline.

### A.1 Verify mask sides and volumes

After `merge_segmentation.py` or `process_full_body_raw.py`:

```bash
PYTHONPATH=src python -c "
from femuralabs.toolkit.fileio.volume import load_volume
from femuralabs.toolkit.imaging.masks import extract_masks
v = load_volume('data/raw/caseXX/combined_seg.nii')
m = extract_masks(v)
for name, b in m.items():
    print(f'{name:<9} {b.voxel_count:>8} {b.volume_ml:>7.1f} mL  x={b.centroid_world[0]:>7.1f}')
print('femur OK' if m['femur_L'].centroid_world[0] > m['femur_R'].centroid_world[0] else 'FEMUR SWAPPED')
"
```

### A.2 Verify a mesh

Confirms `boundary = 0` (mesh is closed), `non_manifold` fraction is under 0.1%, and mesh volume matches voxel volume within 10%:

```bash
PYTHONPATH=src python -c "
from femuralabs.toolkit.fileio.volume import load_volume
from femuralabs.toolkit.imaging.masks import extract_masks
from femuralabs.toolkit.imaging.mesh import mask_to_mesh, signed_volume, edge_incidence
v = load_volume('data/raw/caseXX/combined_seg.nii')
m = extract_masks(v)['femur_R']
verts, faces = mask_to_mesh(m.mask, v.spacing, v.origin, v.direction)
counts = edge_incidence(verts, faces)
print('boundary edges:', counts['boundary'])
print('non-manifold edges:', counts['non_manifold'])
print('mesh volume (mm^3):', round(abs(signed_volume(verts, faces)), 1))
print('voxel volume (mm^3):', round(m.volume_ml * 1000, 1))
"
```

### A.3 Femoral head fit diagnostic

Checks the automatic rule against the hand click and prints the fit radius (which should be 17–25 mm for an adult head):

```bash
PYTHONPATH=src python -c "
import numpy as np
from femuralabs.toolkit.fileio.volume import load_volume
from femuralabs.toolkit.imaging.masks import extract_masks
from femuralabs.toolkit.imaging.mesh import mask_to_mesh
from femuralabs.toolkit.geometry.landmarks import femoral_head_centre
from femuralabs.toolkit.fileio.landmark import load_landmarks
v = load_volume('data/raw/caseXX/combined_seg.nii')
m = extract_masks(v); h = load_landmarks('data/ref/landmarks_caseXX.mrk.json')
for side in ('R', 'L'):
    verts, _ = mask_to_mesh(m[f'femur_{side}'].mask, v.spacing, v.origin, v.direction)
    centre, radius, rms = femoral_head_centre(verts)
    ref = np.array(h[f'femoral_head_{side}'])
    print(f'femur_{side}: err {np.linalg.norm(centre-ref):.2f} mm, radius {radius:.1f} mm')
"
```

A radius over 28 mm or an error over 15 mm means either the medial window is wrong (see `docs/landmarks.md`) or the mask is broken (e.g., metal artifacts, see `docs/data.md` "Traps").

### A.4 Ankle fit diagnostic

```bash
PYTHONPATH=src python -c "
import numpy as np
from femuralabs.toolkit.fileio.volume import load_volume
from femuralabs.toolkit.imaging.masks import extract_masks
from femuralabs.toolkit.imaging.mesh import mask_to_mesh
from femuralabs.toolkit.geometry.landmarks import ankle_centre
from femuralabs.toolkit.fileio.landmark import load_landmarks
v = load_volume('data/raw/caseXX/combined_seg.nii')
m = extract_masks(v); h = load_landmarks('data/ref/landmarks_caseXX.mrk.json')
for side in ('R', 'L'):
    tv, _ = mask_to_mesh(m[f'tibia_{side}'].mask, v.spacing, v.origin, v.direction)
    fv, _ = mask_to_mesh(m[f'fibula_{side}'].mask, v.spacing, v.origin, v.direction)
    centre, info = ankle_centre(tv, fv)
    ref = np.array(h[f'ankle_centre_{side}'])
    print(f'ankle_{side}: err {np.linalg.norm(centre-ref):.2f} mm, plafond_z {info[\"plafond_z\"]:.1f}')
"
```

An error over 8 mm or a `plafond_z` within 3 mm of the tibia bottom means the search window found the malleolar tip, not the plafond.

---

## Appendix B: Flow diagrams

Each time module flow changes, add a diagram. Old sections are never edited — `docs/FLOW.md` is append-only.

```bash
python scripts/dev/draw_flow.py \
  --slug <short-slug> \
  --title "<heading>" \
  --description "<2-4 sentences>" \
  --spec - <<'EOF'
{ "nodes": [...], "edges": [...] }
EOF
```

The command prepends a section above the `<!-- INSERT HERE -->` marker in `docs/FLOW.md`. The PNG goes to `docs/flow/<slug>.png`. Re-running with an existing slug exits non-zero; to regenerate, delete both the section and the PNG first.

---

## Appendix C: Adding a new stage

When you add a new pipeline stage, add a section to this runbook with four parts:

1. **What it does**, one sentence.
2. **The commands**, as a code block.
3. **The expected output**, as a code block, so a reader can diff.
4. **Failure modes**, as a bullet list naming the symptom and its cause.

**Do not add a command that has not been run and verified.** An unrun command is a guess dressed as documentation. If a step depends on GUI clicks you have not actually performed, do not write it — the runbook's value comes from being accurate for the hardware and software versions in `environment.json`.

---

## Appendix D: Verifying a clean checkout

Proves that the files tracked by git reproduce the project. Clones into `/tmp`, runs pytest, runs the CLI, builds the image, runs the container, checks the output.

```bash
bash scripts/dev/clean_check.sh
```

Expected: `pytest -q` passes, the geometry lines print twice (host and container), and the script ends with `clean checkout: all checks passed`.

Run this before trusting a commit. If a file exists in your working tree but was never committed, this script will not see it — that is the point.

---

## Appendix E: Old manual merge (deprecated)

Before `merge_segmentation.py` existed, the merge was done by hand-copying the Slicer snippets. This appendix preserves the procedure for historical reference and for the rare case where a subject's `.labels.csv` is missing or corrupted.

The old snippet hardcoded case01's label values (5, 6, 2, 9, 3, 10). **Do not use it** on any other subject; the label values vary. `merge_segmentation.py` reads the CSV and does this automatically.

If you must do the merge manually, use the Slicer export procedure from §3.2 to produce `thighs_on_full.nii` and `shanks_on_full.nii`, then:

```python
import numpy as np, SimpleITK as sitk
t = sitk.GetArrayFromImage(sitk.ReadImage('thighs_on_full.nii'))
s = sitk.GetArrayFromImage(sitk.ReadImage('shanks_on_full.nii'))
merged = np.zeros_like(t, dtype=np.uint8)
merged[t == <femur_R_source>] = 1
merged[t == <femur_L_source>] = 2
merged[s == <tibia_R_source>] = 3
merged[s == <tibia_L_source>] = 4
merged[s == <fibula_R_source>] = 5
merged[s == <fibula_L_source>] = 6
out = sitk.GetImageFromArray(merged)
out.CopyInformation(thighs)  # NOT optional
sitk.WriteImage(out, 'combined_seg.nii')
```

The `<..._source>` values come from the subject's `.labels.csv` (Slicer writes one next to each export). Getting any of them wrong produces a silent, wrong `combined_seg.nii` — which is why `merge_segmentation.py` exists.

---