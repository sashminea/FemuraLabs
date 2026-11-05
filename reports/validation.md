# Pipeline Validation Report

## 1. Purpose and Status

This report summarises the validation of the FemuraLabs geometric pipeline. **This is a research prototype and is not for clinical use.**

## 2. Data

The pipeline was evaluated on **8 subjects** from the Zenodo record 8302449 (VSDFullBodyBoneReconstruction):

| Internal ID | Zenodo zip | Subject | Layout |
|---|---|---|---|
| case01 | 006.zip | 051Y.F.CT.168 | Standard lower-limb |
| case02 | 023.zip | 074Y.M.CT.521 | Standard lower-limb |
| case03 | 014.zip | 030Y.F.CT.547 | Standard lower-limb |
| case04 | z061.zip | 039Y.F.CT.58316 | Full-body upside-down |
| case05 | z062.zip | 043Y.M.CT.58317 | Full-body upside-down |
| case06 | z063.zip | 072Y.F.CT.58318 | Full-body upside-down (severe metal) |
| case07 | z064.zip | 069Y.M.CT.58314 | Full-body upside-down |
| case08 | z066.zip | 048Y.M.CT.58312 | Full-body upside-down |

Reference masks come from the VSD dataset and are **hollow shells** (cortical only, medullary canal not annotated). Filled volume ratio: femur ≈ 1.3–1.7×, tibia ≈ 1.3–1.8×, fibula ≈ 1.1–1.3×, talus ≈ 1.0–1.2×. Hand landmarks were placed by a single annotator in 3D Slicer on the raw masks. See D048.

## 3. Methods

- **Femoral head**: least-squares sphere fit to the medial 20 mm of the superior 25% of the femur mesh, three iterations of outlier trimming.
- **Knee centre**: bounding box of a 2 mm axial slab at +15 mm above the lowest femoral vertex, shifted (+6.0 mm lateral, −8.5 mm anterior in LPS). See D047.
- **Ankle centre**: maximal-width band in the bottom 30 mm of the tibia (the plafond), midpoint between the medial tibia edge and lateral fibula edge at that level.
- **HKA**: coronal angle between hip-knee and knee-ankle mechanical axes (y-component zeroed). The 3D angle is also recorded (`HKA3D`). See D045.
- **mLDFA / MPTA**: acute angle between mechanical axis and joint line, projected to the coronal plane.
- **Meshing**: marching cubes on the interior-filled mask, scaled to mm, transformed to LPS.
- **TotalSegmentator comparison**: TotalSegmentator v2.18.0 run on a 3 mm-downsampled bounding-box crop per subject, pasted back to the native grid, compared with the filled reference using Dice and axis-corrected HD95. See D046.

## 4. Results

### 4.1 Landmark errors (mm)

| Landmark | Mean (all 8) | Median (all 8) | Mean (clean 6, excl. 04 and 06) |
|---|---|---|---|
| Femoral head R | 9.66 | 2.63 | 2.63 |
| Femoral head L | 6.48 | 2.94 | 2.72 |
| Knee centre R | 4.85 | 4.33 | 4.32 |
| Knee centre L | 5.30 | 4.72 | 4.30 |
| Ankle centre R | 5.98 | 6.56 | 5.58 |
| Ankle centre L | 7.30 | 8.09 | 6.86 |

The femoral head rule is exact on clean subjects (0.5–7 mm, all inside or near the 4–6 mm hand repeat). Cases 04 and 06 fail at 26–36 mm due to deformation and metal, and are excluded from the clean-subject column.

The knee rule was rewritten (D047). Under the previous two-blob rule the mean error was **8.1 mm** with two subjects at 25–27 mm; under the box rule it is **4.85 mm** with worst-case 9.31 mm (case04L, metal).

### 4.2 Alignment angles (degrees)

| Angle | n | Bias | SD | Median abs | Mean abs | Mean abs (clean 6) |
|---|---|---|---|---|---|---|
| HKA R (coronal) | 8 | −0.70 | 2.29 | 1.60 | 1.65 | **0.98** |
| HKA L (coronal) | 8 | +0.17 | 1.62 | 1.56 | 1.26 | **0.98** |
| HKA3D R (reference) | 8 | +1.00 | 2.93 | 1.18 | 1.90 | 1.86 |
| HKA3D L (reference) | 8 | −1.20 | 4.69 | 0.69 | 2.15 | 1.57 |
| mLDFA R | 8 | −0.88 | 1.66 | 0.71 | 1.23 | 0.82 |
| MPTA R | 8 | +0.26 | 0.70 | 0.64 | 0.62 | 0.58 |

On clean subjects, the coronal HKA error is **0.98°**, which is roughly the level of inter-observer disagreement on HKA (typically ~1°) and well inside the 5–10° corrections typical of HTO. The two metal/deformed subjects (04, 06) drive the overall mean to 1.26–1.65°.

**Note on mLDFA/MPTA validation.** The joint-line points (`condyle_medial`, `condyle_lateral`, `plateau_medial`, `plateau_lateral`) are the same hand clicks for the auto and hand angle computations. So the reported difference measures the mechanical-axis contribution to the joint-line angle, with the joint line held fixed. It is not a validation of an automatic joint-line detector. A fully automatic mLDFA/MPTA would need a joint-line rule, which this project does not implement.

### 4.3 Segmentation (TotalSegmentator vs human reference)

The TotalSegmentator comparison was regenerated for case05 after the HD95 axis fix (D046) and the reference-fill (D048). It reports both filled and unfilled Dice. The case01–case03 numbers in earlier runs predate both fixes and are not reported here; regenerating them requires rerunning TotalSegmentator on those subjects.

Case05, 3 mm `--fast` TotalSegmentator on a cropped CT:

| Bone | Dice (filled) | Dice (unfilled) | HD95 (mm) |
|---|---|---|---|
| femur_R | 0.947 | 0.794 | (regenerated after D046) |
| femur_L | ~0.94 | ~0.79 | (regenerated after D046) |
| tibia_R | — | — | (regenerated after D046) |
| tibia_L | — | — | (regenerated after D046) |

Filled Dice ≈ 0.95 confirms that TotalSegmentator fills the medullary canal that the human reference leaves blank; the 0.79 raw Dice measures that annotation-protocol difference, not TotalSegmentator error. HD95 should be regenerated after D046 before quoting; the values in the previous report used the wrong axis scaling.

## 5. Limitations

- **n=8, single annotator.** Descriptive only; no statistical claims of accuracy.
- **Postmortem, supine.** Geometry differs from a standing, weight-bearing patient.
- **Two failure cases.** case04 has severe deformation (widest joint gaps, axial rotation); case06 has bilateral hip and knee arthroplasties with metal beam-hardening. Both are kept for completeness and excluded from the clean-subject column.
- **Hollow reference masks.** All landmark rules and mesh statistics run on the outer surface. Volume in `volume_ml` is the raw shell volume; `volume_filled_ml` is post-fill. TotalSegmentator comparison uses the filled reference.
- **Hand reference noise.** Femoral head repeat ~4–6 mm, knee centre ~3–5 mm, ankle ~2 mm. Rules closer than that are at the noise floor.
- **mLDFA/MPTA are not fully automatic.** The joint line is held at the hand reference (see §4.2).
- **HKA is coronal.** A subject with fixed flexion would have a 3D HKA that differs from the coronal one; that difference is reported separately as `HKA3D`.
- **TotalSegmentator comparison is 3 mm.** Native-resolution runs would likely push Dice higher; see D046 for the axis fix status.

## 6. Not done

- Own trained segmentation model (would require more annotated subjects).
- Fully automatic joint-line landmarks.
- Registration, DRR, osteotomy simulation.
- Multi-annotator reference; inter-observer spread on HKA and joint-line angles.
- Cloud deployment of the full pipeline.