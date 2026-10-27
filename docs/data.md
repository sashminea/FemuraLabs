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

The alignment pipeline needs only femur and tibia. The merged file
(`combined_seg.nii`) contains:

| Label | Bone |
|---|---|
| 0 | Background |
| 1 | Femur_R (was label 5 in thighs) |
| 2 | Femur_L (was label 6 in thighs) |
| 3 | Tibia_R (was label 2 in shanks) |
| 4 | Tibia_L (was label 9 in shanks) |

Anything else in the source segmentations is not written to the merged
file.

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
3. A short Python script reads both files, extracts the four bones by
   their source label values (5, 6, 2, 9), writes them into a new array
   as labels 1-4, and saves the result as `combined_seg.nii` on the
   full-limb grid.
4. Verification: `combined_seg.nii` must be 512 x 512 x 1637 with the
   same spacing as the full volume, and its unique label values must be
   `[0 1 2 3 4]`.


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