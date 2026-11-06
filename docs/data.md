# Data

Two Zenodo records supply the reference data. Neither is committed; `data/` is gitignored. Full citation metadata is in `CITATION.cff`.

| Record | Contents | Licence | DOI |
|---|---|---|---|
| Segmentations and surface models | Pelvis and lower-limb bones, >20 subjects | CC BY-NC-SA 4.0 International | 10.5281/zenodo.8302449 |
| CT collection | Anonymised postmortem whole-body CT | CC BY-NC-SA 3.0 Switzerland | 10.5281/zenodo.8270365 |

The CT collection's description text says "CC BY-NC-SA" without a version; the structured licence field is the binding one and specifies 3.0 Switzerland. Third-party catalogues occasionally misreport the segmentation licence as CC BY 4.0; the record's structured field (4.0) governs the data files.

## Subject-to-Case Mapping

To ensure reproducibility, here is the exact mapping between our internal `caseXX` identifiers and the files in the Zenodo record (`8302449`). You must download these specific zips to reproduce the validation results.

| Internal ID | Zenodo Zip | Subject ID (Patient) | Layout Type | Notes |
|---|---|---|---|---|
| `case01` | `006.zip` | `051Y.F.CT.168` | Lower-Limb | Clean single volume. |
| `case02` | `023.zip` | `074Y.M.CT.521` | Lower-Limb | Clean single volume. |
| `case03` | `014.zip` | `030Y.F.CT.547` | Lower-Limb | Clean single volume. |
| `case04` | `z061.zip` | `039Y.F.CT.58316` | Full-Body | Upside-down, requires H5 transform. Missing talus mask. |
| `case05` | `z062.zip` | `043Y.M.CT.58317` | Full-Body | Upside-down, requires H5 transform. |
| `case06` | `z063.zip` | `072Y.F.CT.58318` | Full-Body | Upside-down. Has severe metal artifacts (bilateral implants). |
| `case07` | `z064.zip` | `069Y.M.CT.58314` | Full-Body | Upside-down, requires H5 transform. |
| `case08` | `z066.zip` | `048Y.M.CT.58312` | Full-Body | Upside-down, requires H5 transform. |

**Note on discarded subjects:** Some zips in the Zenodo record (e.g., `010.zip`) contain split volumes where the pelvis is from one patient and the shanks are from another. These were discarded to maintain anatomical consistency.

## The Three Dataset Layouts

The Zenodo record is highly inconsistent. Subjects ship in one of three layouts. You must identify the layout before preparing the data.

### Layout A: Standard Lower-Limb (e.g., case01–case03)
These subjects ship with a single `SMIR.Lower_limb...nrrd` CT and separate `.seg.nrrd` files. The workflow is **Slicer export + Python merge**. 
- **Pros:** Clean geometry.
- **Cons:** Requires manual GUI clicking.

### Layout B: Full-Body Upside-Down (e.g., case04–case08)
These subjects ship with a full-body CT (`SMIR.Body...nii`), a `Transform-Upside-Down.h5` file, and an `.mrml` scene. The raw CT array is upside down. 
- **Pros:** The H5 transform and MRML scene guarantee perfect alignment.
- **Cons:** Slicer drops the H5 translation on export, breaking the geometry. WSL OOM limits prevent loading the 3.4 GB CT directly into Python.
- **The Solution:** We use `scripts/data/process_full_body_raw.py` to apply the H5 transform mathematically, extract *only* the leg bounding box from the raw CT, combine the segmentations, and center the patient at X=0.

### Layout C: Split Volumes (Discard)
Some subjects ship two separate CT volumes (e.g., `...266` and `...269`). This is fine if they belong to the same patient (load the `.mrml` scene in Slicer to stitch them). However, if the patient IDs differ, the subject is scientifically invalid. **Discard Layout C.**

## Producing `combined_seg.nii`

The pipeline reads a single 8-label NIfTI. The dataset does not ship that way. Here is how the target file is produced.

### Target Label Standard
Regardless of the source layout, every `combined_seg.nii` must have exactly these 8 labels:

| Label | Bone | Source labels (Thighs) | Source labels (Shanks) |
|---|---|---|---|
| 0 | Background | — | — |
| 1 | Femur_R | 5 | — |
| 2 | Femur_L | 6 | — |
| 3 | Tibia_R | — | 2 |
| 4 | Tibia_L | — | 9 |
| 5 | Fibula_R | — | 3 |
| 6 | Fibula_L | — | 10 |
| 7 | Talus_R | — | 4 (or 6) |
| 8 | Talus_L | — | 11 (or 8) |

*Note: Source label numbers vary per subject. The scripts read the `.labels.csv` (Layout A) or the `.seg.nrrd` metadata (Layout B) to map by **name**, not by hardcoded number.*

### Path A: Manual Slicer Export (Layout A)
1. Open the full-limb `.nrrd` in Slicer.
2. Load the `_Reconstruction.seg.nrrd` (thighs) or `_Segmentation.seg.nrrd` (shanks).
3. `Modules → Segment Editor`: Set **Source Volume** to the full-limb CT. Click the **Segment Geometry** icon and apply it. *(This resamples the mask onto the full grid).*
4. `Modules → Segmentations`: **Export to files** as NIfTI (`.nii`).
5. Repeat for both thighs and shanks.
6. Run `scripts/data/merge_segmentation.py`, which reads the `.labels.csv` and merges them into the 8-label format.

### Path B: Python-Only Pipeline (Layout B)
1. Run `scripts/data/process_full_body_raw.py`.
2. This script reads the H5 transform, crops the 3.4 GB full-body CT to the leg bounding box, combines the segmentations, and applies a geometric center so the mid-sagittal plane is exactly at X=0.
3. The output is `ct_cropped.nii` and `combined_seg.nii`, perfectly aligned and right-side up.

## Verification (Any Layout)

Whichever path you use, verify the output immediately:
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
**Expected:** `femur_L x` is positive, `femur_R x` is negative. In LPS, the patient's left is +x. If both are positive, the geometry is shifted (Layout B centering failure). If the signs are swapped, the direction matrix is broken (RAS/LPS confusion).

## Machine Learning Data Preparation

To train the custom SegResNet, the high-resolution native CTs and the hollow reference masks must be standardized into a format suitable for 3D patch extraction.

### 1. The Hollow Shell Problem
The VSD reference segmentations are **cortical shells**; they do not annotate the medullary canal (the trabecular bone and marrow inside). Training a model on hollow masks teaches it to predict hollow bones. 

Before saving any training data, we apply `fill_bone_interior()` to fill the enclosed background in each axial slice. This expands the femur volume by ~1.5× and ensures the model learns solid anatomy.

### 2. Isotropic Resampling
The native scans have varying voxel spacings:
- In-plane: 0.88 mm to 1.27 mm
- Z-axis: 0.5 mm to 0.7 mm

To prevent the model from learning size invariance from only 6 subjects, `prepare_dataset.py` resamples everything to **1.5 mm isotropic**. At 1.5 mm, the volumes are small enough to fit comfortably in RAM (~380 M voxels total) and the patch size (96³) spans 144 mm, which comfortably covers the distal femur (~75-95 mm wide).

### 3. The `.npy` Format
The data is saved as per-case `.npy` files (`caseXX_ct.npy` and `caseXX_seg.npy`):
- **CT**: `int16`, raw Hounsfield Units (HU). Storing as `int16` halves the file size and allows flexible normalization on-the-fly during training.
- **Seg**: `uint8`, the 8 original labels (sides *not* merged).

The manifest file (`scripts/ml/manifest.json`) defines the paths.

Run the preparation script:
```bash
PYTHONPATH=src python scripts/ml/prepare_dataset.py --manifest scripts/ml/manifest.json
```
Outputs go to `data/ml_npy/`, which is later zipped and uploaded to Kaggle for training.

## Traps Worth Remembering

- **`.seg.nrrd` is not a simple labelmap.** Slicer uses it to store a complex scene (segment names, colors, geometries). SimpleITK reads it as a scalar array. Use NIfTI for the pipeline.
- **The Source Volume dropdown does not resample.** You *must* click the **Segment Geometry** icon in Segment Editor before exporting. If you skip it, Slicer exports a crop instead of the full grid.
- **Slicer drops the H5 transform on export.** For full-body scans, never use Slicer to export segmentations. The H5 translation is lost, leaving you with `origin=(0,0,0)`. Use `process_full_body_raw.py` instead.
- **Slicer shows RAS, SimpleITK shows LPS.** Slicer's coordinate display negates X and Y relative to SimpleITK. Do not "fix" the sign in your code to match Slicer.
- **Metal Artifacts break the sphere fit.** Subjects with total hip/knee replacements (e.g., `case06`) cause beam hardening. The segmentations shatter, and `femoral_head_centre` fails (errors > 30 mm). The pipeline does not crash, but the angles for that subject are invalid.
- **`data/` is strictly gitignored.** Never commit raw arrays, `.nii` files, or the `.npy` training data. The repo tracks only the scripts that produce them.
