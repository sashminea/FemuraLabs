# Runbook

This document walks through the entire FemuraLabs pipeline, from environment setup to validation reports. Sections are ordered by the sequence you'd actually follow them in. If you're new to the repo, start at "Quick start".

Every command here was run on the development workstation (WSL2 Ubuntu, 7.7 GB RAM, no GPU) and its output was captured. **Paths in this document are placeholders** (`/path/to/FemuraLabs`, `/path/to/downloads`). You must replace them with the actual paths on your system.

---

## Quick start

If you just want to confirm the repo works, run these three commands. They take ~2 minutes total and require no data.

```bash
cd /path/to/FemuraLabs
source .venv/bin/activate
pytest -q                          # runs the test suite
docker build -t femuralabs-tool .  # ~2 min, downloads ~1.2 GB
docker run --rm femuralabs-tool    # runs the pipeline on a synthetic volume
```

If all three succeed, the code, dependencies, and container are working. Everything below is about real data.

---

## 1. Environment setup

Run this before any other command in a new terminal. Three checks: are you in the right folder, is the venv active, are unexpected files modified.

```bash
cd /path/to/FemuraLabs
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

The test suite covers the array helpers, geometry primitives, mesh algorithms, landmark rules, alignment math, statistical functions, metrics, I/O, the CLI, the report writer, and the HTTP service. It runs in ~2 minutes and is the cheapest check that nothing regressed.

```bash
pytest -q
```

Expected: a line ending with `passed`, no `failed`. `conftest.py` at the project root puts `src/` on the import path, so no `PYTHONPATH` prefix is needed.

If a test fails, the output names the file and line. **Do not change the test to match the code** — change the code, or add an entry to `docs/decisions.md` explaining why the expected value was wrong. 

**Disk space on WSL2:** `pytest` writes ~200 MB of temporary files per run. To prevent the WSL virtual disk from growing without bound, `pytest.ini` redirects `tmp_path` to `/dev/shm/pytest_tmp` (a RAM disk), and `conftest.py` wipes it after every run.

---

## 3. Data preparation

The Zenodo dataset (record 8302449, `VSDFullBodyBoneReconstruction`) ships in **three different layouts**. You need to identify which layout a subject uses before doing anything else.

| Layout | What's in the zip | How we handle it |
|---|---|---|
| **A. Standard lower-limb** | One `SMIR.Lower_limb...nrrd`, four `.seg.nrrd` | Slicer export → `merge_segmentation.py` |
| **B. Full-body upside-down** | One `SMIR.Body...nii`, four `.seg.nrrd`, `Transform-Upside-Down.h5`, `.mrml` | `process_full_body_raw.py` (pure Python) |
| **C. Split volume, mixed patients** | Two separate CT volumes, sometimes from different patients | **Discard this subject.** Cannot be salvaged |

### 3.1 Identify the subject's layout

```bash
python scripts/dev/inventory_dataset.py --dir /path/to/downloads --filter zXXX
```

Replace `zXXX` with the zip number. The script recurses any depth and prints absolute paths categorized by file type. If it lists a `SMIR.Body...nii` plus a `.h5` transform, the subject is Layout B. If it lists a `SMIR.Lower_limb...nrrd`, it's Layout A.

### 3.2 Layout A: Standard lower-limb (e.g., case01–case03)

These subjects ship with a clean full-limb CT (`SMIR.Lower_limb...nrrd`) and two segmentations. 

**Producing the thighs NIfTI:**

1. In 3D Slicer, `File → Add Data`, open the `SMIR.Lower_limb...nrrd`.
2. Confirm in `Modules → Volumes → Volume Information` that dimensions are ~512 × 512 × 1500+.
3. `File → Add Data`, open the `-Pelvis-Thighs_Reconstruction.seg.nrrd`.
4. **`Modules → Segment Editor`** — not Segmentations. Set the **Source Volume** dropdown to the full-limb CT.
5. Click the small icon to the right of Source Volume (the **Segment Geometry** dialog). Confirm dimensions match the CT (~512 × 512 × 1637). Click **OK**. This step is mandatory — without it the export is crop-sized.
6. **`Modules → Segmentations`** — not Segment Editor. Scroll to **"Export to files"**, set format `NIFTI (.nii)`, choose a temporary destination folder, click **Export**.
7. Copy the `.nii` and `.labels.csv` to the project data folder under a fixed name:

```bash
cp /path/to/exports/caseXX/*Pelvis-Thighs_Reconstruction.nii data/raw/caseXX/thighs_on_full.nii
cp /path/to/exports/caseXX/*Pelvis-Thighs_Reconstruction.labels.csv data/raw/caseXX/thighs_on_full.labels.csv
```

**Producing the shanks NIfTI:** repeat steps 3–7 with `-Shanks-Feet_Segmentation.seg.nrrd` (Segmentation, not Reconstruction), saving as `shanks_on_full.nii` / `shanks_on_full.labels.csv`.

**Merge into one multi-label file:**

```bash
PYTHONPATH=src python scripts/data/merge_segmentation.py \
  --thighs data/raw/caseXX/thighs_on_full.nii \
  --shanks data/raw/caseXX/shanks_on_full.nii \
  --out    data/raw/caseXX/combined_seg.nii
```

The script reads each subject's `.labels.csv` to look up source label values by name (e.g., `Femur_R` → some integer that varies per subject), so it does not assume case01's numbers.

**Clean up the intermediates** to save space:
```bash
rm data/raw/caseXX/thighs_on_full.* data/raw/caseXX/shanks_on_full.*
```

### 3.3 Layout B: Full-body upside-down (e.g., case04–case08)

These subjects ship a full-body CT (`SMIR.Body...nii`), separate segmentations, and a `Transform-Upside-Down.h5` file. The raw CT is stored feet-first, so the array is upside down. **Do not use Slicer to export these** — Slicer drops the H5 translation when exporting and the geometry breaks.

Instead, one Python script does everything: it reads the H5 transform, extracts the raw leg bounding box from the CT (bypassing OOM), combines the segmentations, and centers the patient at X=0.

```bash
PYTHONPATH=src python scripts/data/process_full_body_raw.py \
  --ct /path/to/downloads/zXXX/zXXX/SMIR.Body...nii \
  --thighs-seg /path/to/downloads/zXXX/zXXX/...Pelvis-Thighs_Reconstruction.seg.nrrd \
  --shanks-seg /path/to/downloads/zXXX/zXXX/...Shanks-Feet_Segmentation.seg.nrrd \
  --transform /path/to/downloads/zXXX/zXXX/Transform-Upside-Down.h5 \
  --out-dir data/raw/caseXX
```

**Read the log:** each `Mapped` line names the source label value the script found in the CSV, the destination label, and the voxel count. A zero for `Talus_R` or `Talus_L` means the source data did not annotate that bone — this is common in VSD and the pipeline tolerates it.

### 3.4 Verifying any prepared subject

Whichever layout you used, the output is `data/raw/caseXX/combined_seg.nii` with 8 labels. Run the standard check:

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

Expected: `femur_L x` positive, `femur_R x` negative. If the sides are swapped, every downstream angle is wrong.

---

## 4. Landmark placement

Every subject needs 10 hand-placed landmarks. This is the human reference that later stages compare the automatic rules against.

**Setup in Slicer:**

1. Open Slicer.
2. `File → Add Data`, load `data/raw/caseXX/ct_cropped.nii` (Layout B) or the full-limb `.nrrd` (Layout A).
3. `File → Add Data`, load `data/raw/caseXX/combined_seg.nii` as a **Label Map**.
4. Right-click the label map in the Data module → **"Convert label map to segmentation node"**.
5. `Ctrl+Shift+F` to create a Markups node. Rename it to `landmarks_caseXX`.

**Two traps:**
- **Slicer's axial view is radiological.** Patient-right appears on screen-left. `_R` landmarks must be on the screen-LEFT side in axial.
- **The pipeline uses LPS millimetres.** `load_landmarks` reads the file's `coordinateSystem` field and only negates if it says `"RAS"`. Slicer 5.x writes `"LPS"` by default.

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
]:
    if name not in h: continue
    x = h[name][0]
    side_ok = 'OK' if (('_R' in name and x < 0) or ('_L' in name and x > 0)) else 'WRONG SIDE'
    print(f'{name:<20} x={x:>7.1f} {side_ok:<10} dist={min_dist(np.array(h[name]), m[bone].mask):.2f} mm')
"
```

---

## 5. Running the geometric pipeline

The pipeline takes `combined_seg.nii` plus optional landmarks and produces a `summary.json` with mesh statistics, volumes, and alignment angles. 

### 5.1 Single case

```bash
PYTHONPATH=src python scripts/pipeline/pipeline_demo.py \
  --case data/raw/caseXX/combined_seg.nii \
  --out output/caseXX \
  --compare data/ref/landmarks_caseXX.mrk.json \
  --angles \
  --fill-interior
```

The `--fill-interior` flag fills the hollow medullary canal before generating the 3D mesh (essential for accurate sphere fits). The `--knee-method` flag defaults to `box` (the new robust rule).

### 5.2 All cases

Once every subject under `data/raw/` has a `combined_seg.nii` and a `landmarks_caseXX.mrk.json`, run:

```bash
PYTHONPATH=src python scripts/pipeline/run_all_cases.py
```

This loops over `CASES = ["case01", ..., "case08"]` and writes `output/caseXX/summary.json`.

---

## 6. Generating reports

The reports are generated from the JSON summaries, never hand-typed.

```bash
python scripts/pipeline/make_report_tables.py
```

Writes:
- `reports/landmark_errors.md` 
- `reports/angles_case.md`
- `reports/segmentation_errors.md` (requires `reports/data/seg_results_caseXX.json`)

---

## 7. Second method: TotalSegmentator

We compare the human reference masks against TotalSegmentator v2.18.0. 

### 7.1 Installation

```bash
pip install TotalSegmentator
totalseg_set_license -l <academic_license_number>
```

### 7.2 The RAM trap

TotalSegmentator's prediction step is memory-light, but the final resampling step allocates a tensor for all 117 classes at full resolution (~200 GB). On a 7.7 GB RAM machine the OS kills the process with `SIGKILL: 9`. 

**The working solution:** run TotalSegmentator on a tightly cropped CT, then paste the mask back. 

### 7.3 Running on limited RAM

```bash
PYTHONPATH=src python scripts/data/run_totalseg_all.py
```

For each case in `CASES = ["case01", "case02", "case03"]`, it:
1. Crops the CT to the reference mask bounding box.
2. Runs TotalSegmentator on the small crop.
3. Waits for the OOM-killed parent to be replaced by the detached child.
4. Pastes the cropped mask back onto the full grid.

### 7.4 Comparing segmentations

```bash
PYTHONPATH=src python scripts/pipeline/compare_segmentations.py \
  --ref data/raw/caseXX/combined_seg.nii \
  --ts-total output/totalseg/caseXX/segmentation_femurs.nii.gz \
  --ts-app output/totalseg/caseXX_appendicular/segmentation_full.nii.gz \
  --out reports/data/seg_results_caseXX.json
```

The script maps TotalSegmentator's label IDs dynamically and computes Dice/HD95 against the filled reference.

---

## 8. Machine Learning Pipeline

We train a from-scratch 3D SegResNet to segment the bones directly from the CT. This process requires a GPU (Kaggle/Colab T4).

### 8.1 Data Preparation (Local)

This script fills the bone interiors, resamples everything to 1.5 mm isotropic, and saves raw HU as `.npy` files.

1. Create a manifest file (`scripts/ml/manifest.json`) mapping case names to CT/seg paths:
```json
{
  "case01": {"ct": "/path/to/ct.nrrd", "seg": "data/raw/case01/combined_seg.nii"},
  ...
}
```

2. Run the prep script:
```bash
PYTHONPATH=src python scripts/ml/prepare_dataset.py --manifest scripts/ml/manifest.json
```
Outputs go to `data/ml_npy/`. 

### 8.2 Training (Kaggle)

1. **Zip the data**: `zip -r femuralabs_ml_data.zip data/ml_npy/`
2. **Upload to Kaggle**: Create a Dataset (upload the zip) and a second Dataset containing your `.py` scripts (`common.py`, `train.py`, `validate.py`).
3. **Create Notebook**: Add both datasets via the "Input" panel. Enable "GPU T4 x2" and "Internet" in Settings.
4. **Install MONAI**:
```python
!pip install monai==1.3.2 -q
```
5. **Check Paths**: Kaggle mounts datasets with your username. Verify exact paths:
```python
import os
print(os.listdir('/kaggle/input/datasets/<your_username>/femuralabs-ml-scripts'))
```
6. **Run Training**:
```python
!PYTHONPATH=/kaggle/input/datasets/<your_username>/femuralabs-ml-scripts python /kaggle/input/datasets/<your_username>/femuralabs-ml-scripts/train.py \
  --data-dir /kaggle/input/datasets/<your_username>/femuralabs-ml-data \
  --out /kaggle/working/run1 \
  --patch 96 --batch-size 2 --init-filters 16 --epochs 200 --val-every 5
```
Expected: Loss drops from ~1.8 to ~0.4. Validation Dice reaches ~0.93 by epoch 165. Download `best.pt` from the Output panel when done.

### 8.3 Local Validation

Once you have `best.pt` in your local `runs/run1/` folder, run inference and calculate native-resolution metrics:

```bash
PYTHONPATH=src:scripts/ml python scripts/ml/validate.py \
  --checkpoint runs/run1/best.pt \
  --data-dir data/ml_npy \
  --val-cases case07,case08 \
  --out-dir reports/data
```

This script splits the merged left/right classes, upsamples to the native grid, and computes Dice/HD95. The output JSONs are automatically picked up by `make_report_tables.py`.

---

## 9. Docker container

The container packages the geometry pipeline and runs it on a synthetic 8-bone volume. 

```bash
docker build -t femuralabs-tool .
docker run --rm femuralabs-tool
```

---

## 10. HTTP service and Compose

The repo ships a small HTTP service that serves `/health` and `/info`.

```bash
PYTHONPATH=src python -m femuralabs.toolkit.service.serve
# In a second terminal:
curl http://localhost:8000/health
```

---

## Appendix A: Diagnostic scripts

### A.1 Verify mask sides and volumes
*(See Section 3.4)*

### A.2 Femoral head fit diagnostic

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