# Data

Two Zenodo records supply the reference data. Neither is committed; `data/` is gitignored. Full citation metadata is in `CITATION.cff`.

| Record | Contents | Licence | DOI |
|---|---|---|---|
| Segmentations and surface models | Pelvis and lower-limb bones, >20 subjects | CC BY-NC-SA 4.0 | 10.5281/zenodo.8302449 |
| CT collection | Anonymised postmortem whole-body CT | CC BY-NC-SA 3.0 CH | 10.5281/zenodo.8270365 |

The CT collection's description text says "CC BY-NC-SA" without a version; the structured licence field is the binding one and specifies 3.0 CH. Some third-party catalogues misreport the segmentation licence as CC BY 4.0; the record's structured field (4.0) governs the data files, the paper's text covers the paper.

## Case 01 (subject 006)

Working volume `_1`: 512 × 512 × 1637, spacing (0.9765, 0.9765, 0.6997) mm. Do not use the cropped `_2` volume (312 × 205 × 889); it does not reach the ankle.

The reference segmentations are split:

| File | Classes present | Missing |
|---|---|---|
| `Shanks-Feet_Segmentation.seg` | tibia, fibula, tarsals, foot | femur |
| `Thighs_Reconstruction` | sacrum, hip, femur, patella | tibia |

Combined in Slicer onto `_1`'s grid as one multi-label NIfTI; label mapping:
femur=1, tibia=2, fibula=3. See `RUNBOOK.md` for the export step.