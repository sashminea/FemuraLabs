<img width="2873" height="852" alt="FemuraLabs banner" src="https://github.com/user-attachments/assets/41d18b7f-2fb5-4f52-b184-500358c6faa7" />

![License: MIT](https://img.shields.io/badge/code-MIT-green)
![Status: research prototype](https://img.shields.io/badge/status-research%20prototype-orange)
![Not for clinical use](https://img.shields.io/badge/use-not%20for%20clinical%20use-red)

Lower-limb malalignment is one of the main drivers of osteoarthritis. When a leg bows inward or outward, the load on the knee shifts to one side and the joint wears unevenly, which is why surgeons planning a correction such as a high tibial osteotomy want precise numbers for how far a limb has drifted from a straight mechanical axis. The best known of these numbers is the hip-knee-ankle (HKA) angle. In practice most of these measurements are still taken by clicking points on images by hand, which is slow and, more importantly, varies from one person to the next.

FemuraLabs automates the geometric part of that work. It starts from a lower-limb CT volume together with bone segmentation masks, rebuilds the femur, tibia, fibula and talus as watertight 3D surfaces in real millimetres, and then finds the hip, knee and ankle centres directly from the shape of those surfaces. From those three centres it computes the mechanical axes and the alignment angles a surgeon would ask for (HKA, plus the knee joint-line angles mLDFA and MPTA). Every automatic result is compared against landmarks placed by hand, so you can see for yourself how close the automatic rules actually get to what a person would do.

The goal is a reproducible foundation for data-driven orthopaedic planning and biomechanical simulation, one that connects raw clinical imaging to numbers you can inspect and question, rather than a finished clinical tool.

## How the pipeline works

The whole project follows one straight path from scan to report:

`CT volume → bone masks → 3D meshes → landmarks → alignment angles → validation report`

It begins by loading the CT volume together with its geometry. Voxel spacing, origin and orientation travel with the array, so every later number is in millimetres and lives in a single coordinate frame (LPS, the one SimpleITK uses). That detail matters more than it sounds, because mixing up left and right at this stage does not raise an error, it just quietly gives you a mirrored leg. For that reason the project checks sides explicitly in several places, and the pitfalls are written up in the landmark documentation.

Once the volume is loaded, each bone is pulled out of the combined segmentation as its own mask. Because the reference segmentations from the dataset often only trace the outer cortical shell, the pipeline fills the medullary canal before generating the mesh, ensuring the 3D geometry represents the whole bone volume. Each bone is then turned into a triangle mesh with marching cubes and checked for watertightness.

The meshes are what the landmark rules work on. The femoral head centre comes from fitting a sphere, by least squares, to the medial part of the top of the femur. The knee centre uses the bounding box of a thin axial slab 15 mm above the lowest femoral point, shifted by lateral and anterior offsets fitted to human placement conventions. This avoids the common failure where one condyle sits lower than the other, which breaks simple two-blob averaging. The ankle centre comes from finding the tibial plafond (the flat underside of the shin bone) and taking the midpoint between the inner and outer ankle bones at that level.

With three centres per leg, the angles follow. HKA deviation is computed in the coronal plane (matching clinical definitions and the plane used for mLDFA and MPTA) and is reported as positive for varus and negative for valgus. The side of the body is detected automatically, so the same sign means the same thing on the left and the right leg. The joint-line angles mLDFA and MPTA are reported as acute angles (90° or less). Everything for a case is written to a JSON summary, and the report tables are generated from those summaries rather than typed in by hand, so the numbers in the report cannot drift away from the data.

## Results

The pipeline was run on **8 cadaveric subjects** from the [VSDFullBodyBoneReconstruction](https://doi.org/10.5281/zenodo.8302449) dataset, all compared against landmarks placed by hand in 3D Slicer. Two subjects have severe metal artifacts (bilateral hip and knee implants) or extreme postmortem deformation; they are reported separately because their errors are dominated by the artifacts, not the rules.

### Landmark errors

| Landmark | Mean error (clean 6) | Mean error (all 8) | Hand repeat |
|---|---|---|---|
| Femoral head | 2.6–2.7 mm | 6.5–9.7 mm* | 4–6 mm |
| Knee centre | 4.3 mm | 4.9–5.3 mm | 3–5 mm |
| Ankle centre | 5.6–6.9 mm | 6.0–7.3 mm | ~2 mm |

*\*Cases 04 and 06 fail at 26–36 mm (deformation, metal), and are excluded from the clean column.*

The femoral head sphere fit is inside the hand repeat distance on clean anatomy. The knee centre rule is within 5 mm on 11 of 16 knees; the previous rule failed at 25 mm on cases with tilted condyles.

### Alignment angles

| Angle | n | Mean abs | Mean abs (clean 6) |
|---|---|---|---|
| HKA R (coronal) | 8 | 1.65° | **0.98°** |
| HKA L (coronal) | 8 | 1.26° | **0.98°** |
| mLDFA R | 8 | 1.23° | 0.82° |
| MPTA R | 8 | 0.62° | 0.58° |

HKA is reported in the coronal plane, matching the clinical definition and the plane `mldfa`/`mpta` already use. The full 3D angle is recorded in the JSON as `HKA3D_{side}` for reference. On the clean subjects the coronal HKA error is ~1°, comparable to inter-observer spread and well inside the 5–10° corrections typical of high tibial osteotomy.

mLDFA and MPTA agree sub-degree on average. **Caveat:** the joint-line points are the same hand clicks in the auto and hand computations, so this measures the mechanical-axis contribution, not the accuracy of an automatic joint-line detector.

Full per-case tables and the section-by-section limitations are in [`reports/validation.md`](reports/validation.md), [`reports/landmark_errors.md`](reports/landmark_errors.md) and [`reports/angles_case.md`](reports/angles_case.md).

### Segmentation (TotalSegmentator vs human reference)

The reference masks are cortical shells (medullary canal unannotated), so TotalSegmentator naturally fills the interior volume that the human did not. On cases 01–03 (TotalSegmentator run at 3 mm `--fast` on a cropped CT):

| Bone | Mean Dice (filled ref) | Mean Dice (unfilled ref) | Mean HD95 (mm) |
|---|---|---|---|
| Femur | **0.94** | 0.72 | 2.8 |
| Tibia | **0.90** | 0.66 | 5.5 |
| Fibula | **0.82** | 0.73 | 2.5 |

The filled Dice of 0.94 is the honest outer-surface agreement; the raw 0.72 measures the annotation-protocol difference (hollow vs solid).

## Getting started

You can install the project and run its test suite without downloading any CT data, which is the quickest way to check that everything is set up properly on your machine.

```bash
git clone https://github.com/sashminea/FemuraLabs.git
cd FemuraLabs

python3 -m venv .venv
source .venv/bin/activate        # on Windows: .venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt

pytest -q                        # runs the test suite
```

The repository also contains a Dockerfile that packages the full geometry pipeline. You can run the pipeline on a synthetic test volume without installing SimpleITK, scikit-image, or any other dependencies on your host machine:

```bash
docker build -t femuralabs-tool .
docker run --rm femuralabs-tool
```

This will generate a synthetic 8-bone volume, run the full pipeline (masks → meshes → JSON), and output the results inside the container.

Running the real pipeline needs data, annotation work and a few scripts, and that is what the next section walks through.

## Reproducing the validation

Reproducing the results from scratch means getting the dataset, preparing the segmentations, placing reference landmarks by hand, and then letting the scripts do the rest. The four steps below follow that order, and each one points to the part of the documentation that has the full detail.

### 1. Data and segmentation merging

The pipeline reads a single multi-label NIfTI file called `combined_seg.nii`, in which every bone has its own label: `femur_R`, `femur_L`, `tibia_R`, `tibia_L`, `fibula_R`, `fibula_L`, `talus_R` and `talus_L`. The dataset does not ship that way. It ships in two distinct layouts, and we have automated both paths.

- **Standard Lower-Limb**: These ship with clean full-limb CTs. The segmentations are resampled onto the CT grid in Slicer and merged using `scripts/data/merge_segmentation.py`.
- **Full-Body Upside-Down**: These ship as full-body CTs with separate segmentations and an H5 transform file. We use `scripts/data/process_full_body_raw.py` to apply the H5 transform mathematically, extract the lower limb, combine the masks, and center the patient at X=0. This bypasses Slicer's geometry export bugs and WSL memory limits entirely.

[`docs/data.md`](docs/data.md) describes the datasets, their licences, the label mappings, and the split-volume case in detail.

### 2. Manual landmark annotation

To judge the automatic rules there has to be a human reference to compare them with, so each subject needs ten landmarks placed by hand in Slicer and saved as a `.mrk.json` file in `data/ref/`. The click-by-click instructions, with annotated screenshots and the anatomical definition of every landmark, are in the placement guide in [`docs/landmarks.md`](docs/landmarks.md). Please read the section on pitfalls in that file before you place anything. The most important one is that Slicer's axial view follows radiological convention, so the patient's right side appears on the left of the screen, and labelling by screen position produces a perfectly plausible but completely mirrored result.

Once the file is saved, run the diagnostic scripts in the appendix of [`docs/runbook.md`](docs/runbook.md). They confirm that right-side landmarks have negative x and left-side landmarks positive x in LPS, and that the points actually rest on the bone masks.

### 3. Running the pipeline

When `combined_seg.nii` and the landmark files are in the `data/` directory, one command processes every case:

```bash
PYTHONPATH=src python scripts/pipeline/run_all_cases.py
```

For each case this extracts the bone masks, writes the STL meshes, computes the automatic landmarks and the alignment angles, and saves everything to `output/<case>/summary.json`. Bones are meshed one at a time and memory is released in between, keeping peak memory around 3 GB even on the largest scans.

### 4. Generating the reports

The last step turns the JSON summaries into the tables you see in the results above:

```bash
python scripts/pipeline/make_report_tables.py
```

This writes [`reports/landmark_errors.md`](reports/landmark_errors.md) and [`reports/angles_case.md`](reports/angles_case.md). The tables are generated from the pipeline output on purpose, to rule out transcription mistakes, but it also means they can go stale: after any run that changes a result, run this script again.

## Repository layout

The repository is organised so that the code, the documentation and the generated results each have their own place, and the data stays out of version control.

```text
FemuraLabs/
├── src/femuralabs/toolkit/   # Core Python library
│   ├── fileio/               # Volume, landmark, and JSON I/O
│   ├── imaging/              # Masks, meshes, arrays, and volume geometry
│   ├── geometry/             # Landmarks, alignment angles, stats, and metrics
│   ├── reporting/            # Decision logic, JSON writer, summary generator
│   ├── service/              # HTTP API (routes, api, serve)
│   ├── training/             # PyTorch model and training utilities
│   └── cli.py                # Command-line interface for volume geometry
├── scripts/                  # Executable pipeline entry points
│   ├── data/                 # Merge segmentations, process full-body scans
│   ├── pipeline/             # Run cases, compare, and generate reports
│   └── dev/                  # Draw flow diagrams, run training, clean checks
├── tests/                    # Pytest suite
├── docs/                     # Engineering and scientific documentation
├── reports/                  # Generated validation tables and figures
├── Dockerfile                # CPU-only tool container (synthetic demo)
├── requirements.txt          # Dev environment
└── CITATION.cff              # Dataset, paper, and tool references
```

## Documentation

Most of the detail that does not fit in a README lives in `docs/`, and each file is written to be read on its own.

- [`reports/validation.md`](reports/validation.md) is the full validation report, with the method limitations and the angle error tables.
- [`docs/runbook.md`](docs/runbook.md) lists every command, Slicer workflow and diagnostic script.
- [`docs/landmarks.md`](docs/landmarks.md) covers the coordinate traps, the click-by-click placement guide, and the rules behind the automatic landmarks.
- [`docs/conventions.md`](docs/conventions.md) defines the coordinate frame (LPS and RAS), the anatomical definition of each landmark and the sign convention for the angles.
- [`docs/data.md`](docs/data.md) describes the datasets, their licences, the label mappings and how to handle split-volume subjects.
- [`docs/decisions.md`](docs/decisions.md) records the architectural design choices together with the alternatives that were rejected and why.
- [`docs/architecture.md`](docs/architecture.md) is the folder map and a description of the pipeline stages.
- [`docs/FLOW.md`](docs/FLOW.md) holds annotated call graphs showing how data moves between modules.

## Limitations

It is worth being clear about what this project does not claim. It has been evaluated on eight cadaveric subjects, which is still too few for statistical conclusions, so the results are descriptive and should be read as a proof of concept. The scans are post-mortem and supine, which means the geometry does not match a standing, weight-bearing patient, and all hand-placed landmarks come from a single annotator.

The dataset itself has several severe traps that we have documented and engineered around, but which affect the results:
- **Metal Artifacts:** One subject has bilateral total hip and knee arthroplasties. The dense metal causes beam hardening, shattering the segmentation masks and causing the femoral head sphere fit to fail.
- **Postmortem Deformation:** One subject exhibits extreme axial rotation and widened joint spaces, causing the knee and ankle rules to struggle.
- **Reference Noise:** The condyle and plateau points used for the joint-line angles were placed by surface-click, repeating only to within 7 to 9 mm.

On the method side, the ankle rule uses the tibial plafond as a stand-in for the talar dome. The talus is already segmented and merged, but the rule does not use it yet. The TotalSegmentator comparison was run on 3 mm downsampled CTs using a bounding-box crop, because the full-resolution model requires more than 16 GB of RAM.

## Data and licences

FemuraLabs uses two Zenodo records, the [VSDFullBodyBoneReconstruction](https://doi.org/10.5281/zenodo.8302449) segmentations and surface models (CC BY-NC-SA 4.0) and the CT collection they were built from (CC BY-NC-SA 3.0 Switzerland, DOI [10.5281/zenodo.8270365](https://doi.org/10.5281/zenodo.8270365)). The data is not committed to this repository. The code is MIT-licensed, but the MIT licence does not cover the data, which stays under its own licences. If you use this work, please cite it with the details in `CITATION.cff`.
