# Pipeline Validation Report

## Purpose and Status
This report summarizes the validation of the FemuraLabs geometric pipeline. This is a research prototype and is **not for clinical use**. The goal is to measure the accuracy of automated landmark detection and alignment angle computation against a human reference on a small cohort.

## Data
The pipeline was evaluated on **3 subjects** from the Zenodo record 8302449 (VSDFullBodyBoneReconstruction). 
- **case01**: 51Y.F (512 × 512 × 1637)
- **case02**: 74Y.M (512 × 512 × 1969)
- **case03**: 30Y.F (512 × 512 × 1782)

The source CT volumes were segmented in 3D Slicer, merged into a single 8-label volume (femur, tibia, fibula, talus per side), and hand landmarks were placed by a single annotator. Left-side joint-line landmarks were not placed for case02 and case03.

## Results

### Landmark Detection (Automatic vs. Hand-Placed)
The femoral head centre is detected via sphere fit. The knee centre uses a two-condyle split. The ankle centre uses the midpoint of the malleoli at the plafond level. 

*(See `reports/landmark_errors.md` for the full table. Below is a summary of the right-side errors.)*

- **Femoral Head**: Errors are within the hand-placement repeat distance (approx 4-6 mm). The sphere fit matches a second human placer.
- **Knee Centre**: Errors are approx 6-8 mm. The residual is dominated by the hand reference itself, as the right-side hand click sits ~8.7 mm lateral of the mask centroid, while the left sits 0.4 mm away.
- **Ankle Centre**: Errors are approx 4-5 mm. This is about 2× the hand repeat distance, reflecting the reliance on the tibial plafond centroid as a proxy for the talar dome.

### Alignment Angles
Angles were computed from the hand-placed landmarks and compared to angles computed using the automatic centres (where possible).

*(See `reports/angles_case.md` for the full table.)*

- **mLDFA**: Consistently in the 85-87° range across subjects, matching expected anatomical norms.
- **MPTA**: Shows wide variance (71° to 87°). This reflects true anatomical variance (e.g., varus tilt) captured by the hand landmarks, as well as the documented 7-9 mm surface-click noise on the plateau landmarks.
- **HKA**: Ranges from -3.7° (valgus) to +6.2° (varus), consistent with the cadaveric subject population.

## Limitations
- **n=3**: The cohort is too small for statistical claims. The results are descriptive.
- **Cadaveric Data**: The scans are of postmortem subjects. The geometry does not perfectly match a standing patient.
- **Reference Noise**: Surface-click landmarks (condyles, plateaus) have a documented repeatability of 7-9 mm, which limits the degree-level validation of joint-line angles.
- **Talus Proxy**: The automatic ankle rule uses the tibial plafond as a proxy for the talus. The talus is visible in the segmentation but not yet used in the automatic rule.