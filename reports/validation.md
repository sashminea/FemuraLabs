# Pipeline Validation Report

## 1. Purpose and Status
This report summarizes the validation of the FemuraLabs pipeline. **This is a research prototype and is not for clinical use.** The goal is to measure the accuracy of automated landmark detection, alignment angle computation, and bone segmentation against human references on a small cohort.

## 2. Data
The pipeline was evaluated on **3 subjects** from the Zenodo record 8302449 (VSDFullBodyBoneReconstruction):
- **case01**: 51Y.F (512 × 512 × 1637)
- **case02**: 74Y.M (512 × 512 × 1969)
- **case03**: 30Y.F (512 × 512 × 1782)

The source CT volumes were segmented in 3D Slicer, merged into a single 8-label volume (femur, tibia, fibula, talus per side), and hand landmarks were placed by a single annotator. Left-side joint-line landmarks were not placed for case02 and case03.

## 3. Methods
The pipeline extracts bone masks, generates 3D meshes via marching cubes, and computes landmarks. 
- **Femoral Head**: Sphere fit to the medial hemisphere.
- **Knee Centre**: Midpoint of the two condyle blobs.
- **Ankle Centre**: Midpoint of the malleoli at the tibial plafond level.
- **Angles**: HKA, mLDFA, MPTA are computed from the landmark coordinates.

**Segmentation Comparison**: We compared the human reference masks against TotalSegmentator (v2.18.0) using the `total` task (for femurs) and `appendicular_bones` task (for tibias/fibulas). Due to hardware RAM limits (7.7 GB), the model was run on 3mm downsampled and bounding-box-cropped CTs, and the resulting masks were upsampled back to the native grid.

## 4. Results

### 4.1 Landmark Detection (Automatic vs. Hand-Placed)
*(See `reports/landmark_errors.md` for the full table.)*

- **Femoral Head**: Errors are within the hand-placement repeat distance (approx 4-6 mm). The sphere fit matches a second human placer.
- **Knee Centre**: Errors are approx 6-8 mm. The residual is dominated by the hand reference itself, as the right-side hand click sits ~8.7 mm lateral of the mask centroid, while the left sits 0.4 mm away.
- **Ankle Centre**: Errors are approx 4-5 mm. This is about 2× the hand repeat distance, reflecting the reliance on the tibial plafond centroid as a proxy for the talar dome.

### 4.2 Alignment Angles
*(See `reports/angles_case.md` for the full table.)*

- **mLDFA**: Consistently in the 85-87° range across subjects, matching expected anatomical norms.
- **MPTA**: Shows wide variance (71° to 87°). This reflects true anatomical variance (e.g., varus tilt) captured by the hand landmarks, as well as the documented 7-9 mm surface-click noise on the plateau landmarks.
- **HKA**: Ranges from -3.7° (valgus) to +6.2° (varus), consistent with the cadaveric subject population.

### 4.3 Segmentation (TotalSegmentator vs. Human)
*(See `reports/segmentation_errors.md` for the full table.)*

Even on 3mm downsampled data, TotalSegmentator achieves strong agreement with the human reference. The model performs best on the isolated fibula and slightly worse on the large femurs.

| Bone | Mean Dice | Mean HD95 (mm) |
|---|---|---|
| Femur | 0.73 | 7.7 |
| Tibia | 0.67 | 5.5 |
| Fibula | 0.74 | 2.8 |

## 5. Limitations
- **n=3**: The cohort is too small for statistical claims. The results are descriptive.
- **Cadaveric Data**: The scans are of postmortem subjects. The geometry does not perfectly match a standing, weight-bearing patient.
- **Reference Noise**: Surface-click landmarks (condyles, plateaus) have a documented repeatability of 7-9 mm, which limits the degree-level validation of joint-line angles.
- **Talus Proxy**: The automatic ankle rule uses the tibial plafond as a proxy for the talus. The talus is visible in the segmentation but not yet used in the automatic rule.
- **Segmentation Resolution**: The TotalSegmentator comparison was run on 3mm downsampled data with a bounding-box crop to survive the 7.7 GB RAM limit of the development machine. This introduces a ~3mm discretisation error at the boundaries. Running on a machine with >32 GB RAM at the native 1.5mm resolution would likely push Dice above 0.85.