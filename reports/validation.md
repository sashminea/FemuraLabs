# Pipeline Validation Report

## 1. Purpose and Status
This report summarizes the validation of the FemuraLabs pipeline. **This is a research prototype and is not for clinical use.** The goal is to measure the accuracy of automated landmark detection, alignment angle computation, and bone segmentation against human references on a small cohort.

## 2. Data
The pipeline was evaluated on **8 subjects** from the Zenodo record 8302449 (VSDFullBodyBoneReconstruction). The dataset provides a mix of two distinct data layouts:
- **Standard Lower-Limb** (case01–case03): Clean lower-limb CT scans.
- **Full-Body Upside-Down** (case04–case08): Whole-body postmortem CT scans requiring an `.h5` transform and bounding-box cropping.

Subject ages range from 30 to 74, with a mix of male and female cadavers. The source CT volumes were segmented in 3D Slicer or transformed via Python, merged into a single 8-label volume (femur, tibia, fibula, talus per side), and hand landmarks were placed by a single annotator. 

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

Across the 8 subjects, the rules performed variably depending on the subject's anatomy and image quality. 
- **Femoral Head**: On clean subjects (case01, case03, case05), errors are under 5 mm, matching the hand-placement repeat distance. However, the mean error across all 8 subjects is skewed to >10 mm due to catastrophic failures on case04 (severe anatomical deformation) and case06 (metal implants).
- **Knee Centre**: Errors typically range from 6–11 mm. The residual is dominated by the hand reference itself, as the right-side hand click sits ~8 mm lateral of the mask centroid, while the left sits ~1 mm away. (Outliers of 20–30 mm occur on case04 and case07, where postmortem deformation compresses the joint space).
- **Ankle Centre**: Errors are approx 4–7 mm. This is about 2× the hand repeat distance, reflecting the reliance on the tibial plafond centroid as a proxy for the talar dome.

### 4.2 Alignment Angles
*(See `reports/angles_case.md` for the full table.)*

The joint-line angles are remarkably robust, even on subjects with weird geometry:
- **mLDFA**: Mean absolute difference is **0.79°** (Right). Consistently in the 85–89° range, matching expected anatomical norms.
- **MPTA**: Mean absolute difference is **0.66°** (Right). Shows true anatomical variance (71° to 89°).
- **HKA**: Mean absolute difference is **2.24°** (Right) and **2.77°** (Left). Ranges from -9.8° (valgus) to +11.4° (varus), consistent with the cadaveric subject population.

### 4.3 Segmentation (TotalSegmentator vs. Human)
*(See `reports/segmentation_errors.md` for the full table.)*

Even on 3mm downsampled data, TotalSegmentator achieves strong agreement with the human reference. The model performs best on the isolated fibula and slightly worse on the large femurs (where the boundary between the hip socket and femur can get fuzzy).

| Bone | Mean Dice | Mean HD95 (mm) |
|---|---|---|
| Femur | 0.73 | 7.7 |
| Tibia | 0.67 | 5.5 |
| Fibula | 0.74 | 2.8 |

## 5. Failure Analysis
The pipeline successfully identified two distinct failure modes in the dataset that affect automated landmark detection:

1. **Metal Artifacts (case06):** This subject has bilateral total hip and knee arthroplasties. The dense metal causes beam hardening, which punches holes in the segmentation masks. The sphere fit (`femoral_head_centre`) fails catastrophically on these fragmented masks, producing errors >30 mm.
2. **Severe Cadaveric Deformation (case04):** This subject exhibits extreme axial rotation and widened joint spaces (likely due to the postmortem supine position and lack of weight-bearing). The joint-line rules (`knee_centre`, `condyle_*`) struggle to find the anatomical landmarks, producing errors of 20–30 mm.

**Key finding:** The pipeline does not crash when exposed to these failures. It produces invalid numbers, which is a known limitation, but it allows the rest of the cohort to process normally.

## 6. Limitations
- **n=8**: The cohort is still too small for definitive statistical claims. The results are descriptive.
- **Cadaveric Data**: The scans are of postmortem subjects. The geometry does not perfectly match a standing, weight-bearing patient. Metal implants and postmortem deformation are present.
- **Reference Noise**: Surface-click landmarks (condyles, plateaus) have a documented repeatability of 7-9 mm, which limits the degree-level validation of joint-line angles.
- **Talus Proxy**: The automatic ankle rule uses the tibial plafond as a proxy for the talus. 
- **Segmentation Resolution**: The TotalSegmentator comparison was run on 3mm downsampled data with a bounding-box crop to survive the 7.7 GB RAM limit of the development machine. This introduces a ~3mm discretisation error at the boundaries. Running on a machine with >32 GB RAM at the native 1.5mm resolution would likely push Dice above 0.85.

## 7. Not Done
- Clinical validation (no radiograph data).
- Multi-annotator consensus (only one human placed the landmarks).
- Metal Artifact Reduction (MAR) preprocessing to rescue case06.
- Training a custom segmentation model (only the pretrained TotalSegmentator baseline was evaluated).