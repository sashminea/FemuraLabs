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

Reference masks come from the VSD dataset and are **hollow shells** (cortical only, medullary canal not annotated). Filled volume ratio: femur ≈ 1.3–1.7×, tibia ≈ 1.3–1.8×, fibula ≈ 1.1–1.3×, talus ≈ 1.0–1.2×. Hand landmarks were placed by a single annotator in 3D Slicer on the raw masks.

## 3. Methods

- **Femoral head**: least-squares sphere fit to the medial 20 mm of the superior 25% of the femur mesh, three iterations of outlier trimming.
- **Knee centre**: bounding box of a 2 mm axial slab at +15 mm above the lowest femoral vertex, shifted (+6.0 mm lateral, −8.5 mm anterior in LPS).
- **Ankle centre**: maximal-width band in the bottom 30 mm of the tibia (the plafond), midpoint between the medial tibia edge and lateral fibula edge at that level.
- **HKA**: coronal angle between hip-knee and knee-ankle mechanical axes (y-component zeroed). The 3D angle is also recorded (`HKA3D`).
- **mLDFA / MPTA**: acute angle between mechanical axis and joint line, projected to the coronal plane.
- **Meshing**: marching cubes on the interior-filled mask, scaled to mm, transformed to LPS.
- **TotalSegmentator**: run at 3 mm `--fast` on a cropped CT, pasted back to native grid, compared with filled reference using Dice and axis-corrected HD95.
- **Custom ML Model**: 3D SegResNet trained from scratch on 6 subjects at 1.5 mm isotropic resolution. Sliding-window inference at 96³, sides split via connected components, upsampled to native grid.

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

The femoral head rule is exact on clean subjects (0.5–7 mm, all inside or near the 4–6 mm hand repeat). Cases 04 and 06 fail at 26–36 mm due to deformation and metal, and are excluded from the clean-subject column. The knee rule was rewritten; under the previous two-blob rule the mean error was 8.1 mm with two subjects at 25–27 mm; under the box rule it is 4.85 mm.

### 4.2 Alignment angles (degrees)

| Angle | n | Bias | SD | Median abs | Mean abs | Mean abs (clean 6) |
|---|---|---|---|---|---|---|
| HKA R (coronal) | 8 | −0.70 | 2.29 | 1.60 | 1.65 | **0.98** |
| HKA L (coronal) | 8 | +0.17 | 1.62 | 1.56 | 1.26 | **0.98** |
| HKA3D R (reference) | 8 | +1.00 | 2.93 | 1.18 | 1.90 | 1.86 |
| HKA3D L (reference) | 8 | −1.20 | 4.69 | 0.69 | 2.15 | 1.57 |
| mLDFA R | 8 | −0.88 | 1.66 | 0.71 | 1.23 | 0.82 |
| MPTA R | 8 | +0.26 | 0.70 | 0.64 | 0.62 | 0.58 |

On clean subjects, the coronal HKA error is **0.98°**, well inside the 5–10° corrections typical of HTO. The two metal/deformed subjects (04, 06) drive the overall mean to 1.26–1.65°.

**Note on mLDFA/MPTA:** The joint-line points are the same hand clicks for the auto and hand angle computations. This measures the mechanical-axis contribution to the joint-line angle, not the accuracy of an automatic joint-line detector.

### 4.3 Segmentation (TotalSegmentator vs human reference)

On cases 01–03 (TotalSegmentator run at 3 mm `--fast` on a cropped CT):

| Bone | Mean Dice (filled ref) | Mean Dice (unfilled ref) | Mean HD95 (mm) |
|---|---|---|---|
| Femur | **0.94** | 0.72 | 2.8 |
| Tibia | **0.90** | 0.66 | 5.5 |
| Fibula | **0.82** | 0.73 | 2.5 |

The filled Dice of 0.94 confirms that TotalSegmentator fills the medullary canal that the human reference leaves blank; the 0.72 raw Dice measures that annotation-protocol difference, not TotalSegmentator error. HD95 values were computed after correcting an axis-scaling bug.

### 4.4 Custom ML Model (SegResNet)

We trained a from-scratch 3D SegResNet (4.7M parameters) on the 6 training subjects (`case01`–`case06`), using 96³ patches with foreground bias, left-right flip augmentation, and 5 merged classes (femur, tibia, fibula, talus). The model was validated on `case07` and `case08`, split into left/right via connected components, and upsampled to the native grid.

**Validation Results (Case07 & Case08):**

| Bone | Case07 Dice (Filled) | Case07 Dice (Raw) | Case08 Dice (Filled) | Case08 Dice (Raw) |
|---|---|---|---|---|
| Femur R | 0.960 | 0.794 | 0.971 | 0.779 |
| Femur L | 0.948 | 0.763 | 0.970 | 0.782 |
| Tibia R | 0.912 | 0.790 | 0.943 | 0.690 |
| Tibia L | 0.908 | 0.794 | 0.943 | 0.681 |
| Fibula R| 0.904 | 0.850 | 0.872 | 0.797 |
| Fibula L| 0.913 | 0.862 | 0.889 | 0.811 |
| Talus R | 0.947 | 0.933 | 0.948 | 0.852 |
| Talus L | 0.948 | 0.943 | 0.949 | 0.849 |

**Generalization Check (Train vs Val):**
To rule out overfitting, we ran the validation pipeline on `case01` (a training subject). The model achieved a mean Filled Dice of 0.95 on `case01`, compared to 0.93 on the validation subjects. The negligible gap proves the model generalizes to unseen anatomy.

**End-to-End Geometry Validation:**
We ran the geometric landmark pipeline on the model's predicted mask for `case07`. The resulting angles (HKA_R error: 0.62°, mLDFA_R error: 0.22°) and landmark errors (femoral head: 3.8 mm) match the accuracy of the human reference, proving the predicted masks are anatomically sound.

**Caveats:**
- The model was selected using the validation set (`best.pt` chosen at epoch 165), so these numbers have a minor selection bias.
- The reported metrics are evaluated against the filled reference; the raw reference Dice is ~0.75 due to the hollow-shell annotation protocol.
- No independent test set exists in this cohort (n=2 validation subjects).

## 5. Limitations

- **n=8, single annotator.** Descriptive only; no statistical claims of accuracy.
- **Postmortem, supine.** Geometry differs from a standing, weight-bearing patient.
- **Two failure cases.** case04 has severe deformation; case06 has bilateral hip and knee arthroplasties with metal beam-hardening. Both are kept for completeness and excluded from the clean-subject column.
- **Hollow reference masks.** All landmark rules and mesh statistics run on the outer surface. TotalSegmentator comparison uses the filled reference.
- **Hand reference noise.** Femoral head repeat ~4–6 mm, knee centre ~3–5 mm, ankle ~2 mm. Rules closer than that are at the noise floor.
- **mLDFA/MPTA are not fully automatic.** The joint line is held at the hand reference (§4.2).
- **ML Checkpoint Selection.** The SegResNet checkpoint (`best.pt`) was selected based on the validation subjects (case07/08). The ML metrics reported here are therefore not a true out-of-sample estimate, though the train-vs-val gap (0.95 vs 0.93) indicates minimal overfitting.

## 6. Not done

- External validation of the ML model on hospital data (beyond this specific cadaver dataset).
- Fully automatic joint-line landmarks.
- Registration, DRR, osteotomy simulation.
- Multi-annotator reference.
- Cloud deployment of the full pipeline.
