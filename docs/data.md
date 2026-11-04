# Data

Two Zenodo records supply the reference data. Neither is committed;
`data/` is gitignored. Full citation metadata is in `CITATION.cff`.

| Record | Contents | Licence | DOI |
|---|---|---|---|
| Segmentations and surface models | Pelvis and lower-limb bones, >20 subjects | CC BY-NC-SA 4.0 International | 10.5281/zenodo.8302449 |
| CT collection | Anonymised postmortem whole-body CT | CC BY-NC-SA 3.0 Switzerland | 10.5281/zenodo.8270365 |

The CT collection's description text says "CC BY-NC-SA" without a version;
the structured licence field is the binding one and specifies 3.0
Switzerland. Third-party catalogues occasionally misreport the segmentation
licence as CC BY 4.0; the record's structured field (4.0) governs the data
files.

## Case 01 (subject 006)

The subject was downloaded as `006.zip` and extracted into
`data/raw/case01/`. The archive contains:

| File | What it is |
|---|---|
| `SMIR.Lower_limb.051Y.F.CT.168.nrrd` | Full lower-limb CT, 512 x 512 x 1637 |
| `SMIR.Lower_limb.051Y.F.CT.168_1/CT.168.nrrd` | Same volume (Slicer's split naming) |
| `SMIR.Lower_limb.051Y.F.CT.168_2/CT.168.nrrd` | Pelvis-thighs crop, 312 x 205 x 889 |
| `...-Pelvis-Thighs.nrrd` | Pelvis-thighs crop volume |
| `...-Shanks-Feet.nrrd` | Shanks-feet crop volume |
| `...-Pelvis-Thighs_Reconstruction.seg.nrrd` | Segmentation on the pelvis-thighs crop |
| `...-Pelvis-Thighs_Segmentation.seg.nrrd` | Alternative segmentation, same crop |
| `...-Shanks-Feet_Reconstruction.seg.nrrd` | Segmentation on the shanks-feet crop |
| `...-Shanks-Feet_Segmentation.seg.nrrd` | Alternative segmentation, same crop |
| `...-ROI.acsv`, `*.json`, `*.Zone.Identifier` | Metadata, colour tables, Windows download markers. Not needed |

Use the `_1` volume as the working volume (it is the only one that reaches
from hip to ankle). Use `Pelvis-Thighs_Reconstruction.seg.nrrd` for the
femur and `Shanks-Feet_Segmentation.seg.nrrd` for the tibia (these are the
two files whose contents were verified against the segment lists below).

**Working volume geometry.** 512 x 512 x 1637, spacing
(0.9765625, 0.9765625, 0.6997555) mm, origin (249.5, 392.5, 119.7) mm,
ITK-to-RAS direction matrix diag(-1, -1, 1). Slicer shows this in RAS;
SimpleITK shows the same file in LPS, so x and y are negated between the
two viewers.

## Handling split-volume subjects (e.g., case02)

Not every subject ships as a single full-limb volume. Some (like subject 045Y.F in `010.zip`) are split into two distinct CT volumes:
- `...CT.266` (Pelvis-Thighs region, upper half, ~997 slices)
- `...CT.269` (Shanks-Feet region, lower half, ~763 slices)

**The Trap:** It is tempting to export the segmentations from each half and stack them in Python. This fails because the two volumes are cropped independently; the Z-origins may not align perfectly, and the slice spacings can differ slightly, leading to truncated masks (e.g., a tibia that is only 95 mL instead of 150 mL).

**The Solution:** The authors provide an MRML scene file (`SMIR.Lower_limb.045Y.F.CT.mrml`) in the parent directory. Loading this scene in 3D Slicer automatically loads the original, unified full-limb CT volume and places both the pelvis and shank segmentations on the correct grid. From there, the standard export procedure (Segment Geometry → Export to files) works exactly as it does for case01 and case03.

**Fallback:** If the MRML file is missing or fails to load, the manual `stack_segmentation.py` script exists, but it is a last resort. Always prefer the MRML scene.

## Segment labels

Both source segmentations carry a **Threshold-200-MAX** segment at label 1
that is an artefact of the annotation workflow, not a bone. Ignore it.

**Thighs file** (`Pelvis-Thighs_Reconstruction.seg.nrrd`):

| Label | Name |
|---|---|
| 2 | Sacrum |
| 3 | Hip_R |
| 4 | Hip_L |
| 5 | Femur_R |
| 6 | Femur_L |
| 7 | Patella_R |
| 8 | Patella_L |

**Shanks file** (`Shanks-Feet_Segmentation.seg.nrrd`):

| Label | Name |
|---|---|
| 2 | Tibia_R |
| 3 | Fibula_R |
| 4 | Talus_R |
| 5 | Calcaneus_R |
| 6 | Tarsals_R |
| 7 | Metatarsals_R |
| 8 | Phalanges_R |
| 9 | Tibia_L |
| 10 | Fibula_L |
| 11 | Talus_L |
| 12 | Calcaneus_L |
| 13 | Tarsals_L |
| 14 | Metatarsals_L |
| 15 | Phalanges_L |

The alignment pipeline needs femur, tibia and fibula. Fibula is only
used by the ankle-centre rule (the lateral malleolus is part of the
fibula, not the tibia; see `docs/landmarks.md`, ankle_centre). The
merged file (`combined_seg.nii`) contains:

| Label | Bone | Source label | Source file |
|---|---|---|---|
| 0 | Background | — | — |
| 1 | Femur_R | 5 | thighs |
| 2 | Femur_L | 6 | thighs |
| 3 | Tibia_R | 2 | shanks |
| 4 | Tibia_L | 9 | shanks |
| 5 | Fibula_R | 3 | shanks |
| 6 | Fibula_L | 10 | shanks |

The source-label column is the mapping the merge script uses. It is
written out explicitly rather than derived by position, so any future
reader can confirm the mapping against the `.labels.csv` files that
Slicer exports alongside each `.seg.nrrd`.

Anything else in the source segmentations (patella, talus, calcaneus,
tarsals, metatarsals, phalanges, hip, sacrum) is not written to the
merged file.

## Producing `combined_seg.nii`

Full procedure in `docs/runbook.md`, section "Combining the two reference
segmentations". Summary:

1. Both source `.seg.nrrd` files are loaded in 3D Slicer onto the full
   `_1` volume and resampled onto that grid via the "Segment geometry"
   dialog.
2. Each is exported as NIfTI via "Export to files". The export dialog
   does not let you set the filename; Slicer uses the segmentation's own
   name. The two outputs are renamed after copying to WSL:
   `thighs_on_full.nii` and `shanks_on_full.nii`.
3. A short Python script reads both files, extracts the six bones by
   their source label values (thighs 5, 6 → femur_R, femur_L;
   shanks 2, 9, 3, 10 → tibia_R, tibia_L, fibula_R, fibula_L), writes
   them into a new array as labels 1-6, and saves the result as
   `combined_seg.nii` on the full-limb grid. The mapping is explicit
   per source label value, not derived from source-file order.
4. Verification: `combined_seg.nii` must be 512 x 512 x 1637 with the
   same spacing as the full volume, and its unique label values must be
   `[0 1 2 3 4 5 6]`. Expected voxel counts on case01:
   femur_R≈497k, femur_L≈453k, tibia_R≈307k, tibia_L≈288k,
   fibula_R≈77k, fibula_L≈77k. A zero at any of 1-6 means the
   merge script mapped no voxels — check the source label value in
   that row against `shanks_on_full.labels.csv` or
   `thighs_on_full.labels.csv`.


## Traps worth remembering

- **`.seg.nrrd` is not a simple labelmap.** SimpleITK reads it as an array
  but not necessarily as the labels you expect; use NIfTI for anything
  downstream.
- **The Source Volume dropdown in the Segmentations module does not
  resample on export.** "Export to files" writes the segmentation's
  original geometry (the crop). Resampling requires either "Specify
  geometry" with "Resample labelmaps" ticked, or "Export visible segments
  to binary labelmap".
- **The crop volumes look like the full volume in a file listing.** The
  only reliable signal is size: 512 x 512 x 1637 is full-limb,
  312 x 205 x 889 and smaller are crops. Check sizes before loading.
- **`data/` is gitignored.** Nothing under it is ever committed.
- **`.nii` and `.nii.gz` are interchangeable for reading; the extension
  matters only for writing.** SimpleITK detects the format from the file
  signature, so a `.nii.gz` renamed to `.nii` reads correctly and vice
  versa. On writing, `sitk.WriteImage(image, path)` chooses the output
  format from `path`'s extension: `.nii.gz` writes gzipped NIfTI, `.nii`
  writes uncompressed. The array contents are identical either way. This
  pipeline uses `.nii` by default because it saves a decompression step
  on every read; switch a file to `.nii.gz` by renaming the output path
  in the `WriteImage` call, no code change needed.
- **Slicer shows RAS, SimpleITK shows LPS.** For `combined_seg.nii`,
  Slicer's "Volume Information" reports origin (249.5, 392.5, 119.7);
  SimpleITK returns (−249.5, −392.5, 119.7). Same point, x and y
  negated. `docs/runbook.md`'s load_volume check reports the LPS form;
  do not "fix" the sign by comparing against Slicer.
- **The merge script must be auditable.** It maps source label values
  to merged labels one number at a time, not by order of first
  appearance, not by loop index. On case01 the mapping is
  thighs {5→1, 6→2}, shanks {2→3, 9→4, 3→5, 10→6}. A positional
  mapping silently gives a wrong answer the day a subject's source
  labels arrive in a different order, and there is no error message.
  The table in "Segment labels" above is the authoritative mapping;
  the merge script must match it line for line.
- **Split-volume subjects have an MRML shortcut.** Some Zenodo zips (like subject 045Y.F in `010.zip`) contain two separate CT volumes (`...266` and `...269`) instead of one full-limb volume. Do not try to stack these in Python. Instead, open the `...mrml` scene file in Slicer. It automatically loads the unified full-limb volume and aligns both halves. For standard single-volume subjects, just load the `.nrrd` directly.
- **Split-volume subjects with an external transform (e.g., z061) require manual geometry reconstruction.** Some subjects in the Zenodo record (like `z061`) are stored upside down and split into two halves, accompanied by a `Transform-Upside-Down.h5` file. Opening the MRML scene in Slicer fixes the visual 3D view, but **Slicer exports the NIfTI labelmap with identity geometry** (`origin=(0,0,0)`, `direction=identity`). If you merge this with the raw crop geometry, both legs will end up on the positive X side of the coordinate system. 
  
  **The fix:** Run `scripts/data/fix_upside_down_geometry.py`. It flips the X and Z axes to correct the upside-down orientation, and mathematically shifts the X origin so the midpoint between the two femurs sits exactly at `X=0`. This restores anatomical left/right symmetry without altering the shape of the bones.
- **The `SMIR.Body...nii` file is a full-body CT scan, not a lower-limb crop.** The dataset provides whole-body CTs, and the `Lower_limb...nrrd` files are cropped versions used for segmentation. Do not attempt to load the raw `.nii` alongside a manually fixed `combined_seg.nii`—they will not align. For landmarking, always open the MRML scene, which applies the `Transform-Upside-Down.h5` to the full-body CT and aligns the original segmentations. Place landmarks directly on the original segmentations in the scene.

### The Full-Body vs. Cropped Trap

The Zenodo record (8302449) is highly inconsistent. You will encounter three types of subjects:
1. **Clean Lower-Limb**: A single `SMIR.Lower_limb...nrrd` with correctly aligned segmentations. (e.g., case01, case03).
2. **Split Volumes**: Separate `Pelvis-Thighs` and `Shanks-Feet` volumes. Sometimes these are the same patient, but **often they are different patients** combined into one zip. Always check the `PatientID` in the filenames. If they differ, discard the subject.
3. **Full-Body with H5 Transform**: A raw `SMIR.Body...nii` CT and a `Transform-Upside-Down.h5` file. 

**Why the H5 file matters:** The full-body CTs were scanned feet-first or head-first, meaning the raw `.nii` array is upside down. The MRML scene applies the H5 transform to orient it correctly. When Slicer exports a labelmap from this scene, it strips the affine transform (leaving `origin=(0,0,0)`) and applies the rotation to the voxel array. 

**Do not load the raw `.nii` alongside a manually fixed `combined_seg.nii`.** They will not align visually. Always use the MRML scene for landmarking, or follow the full-body crop pipeline in the runbook.