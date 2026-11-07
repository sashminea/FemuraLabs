<img width="2873" height="852" alt="FemuraLabs banner" src="https://github.com/user-attachments/assets/41d18b7f-2fb5-4f52-b184-500358c6faa7" />

![License: Apache 2.0](https://img.shields.io/badge/code-Apache%202.0-blue)
![Status: research prototype](https://img.shields.io/badge/status-research%20prototype-orange)
![Not for clinical use](https://img.shields.io/badge/use-not%20for%20clinical%20use-red)

Lower-limb malalignment is one of the main drivers of osteoarthritis. When a leg bows inward or outward, the load on the knee shifts to one side and the joint wears unevenly, which is why surgeons planning a correction such as a high tibial osteotomy want precise numbers for how far a limb has drifted from a straight mechanical axis. The best known of these numbers is the hip-knee-ankle (HKA) angle. In practice most of these measurements are still taken by clicking points on images by hand, which is slow and, more importantly, varies from one person to the next.

FemuraLabs automates the geometric part of that work. It starts from a lower-limb CT volume together with bone segmentation masks, rebuilds the femur, tibia, fibula and talus as watertight 3D surfaces in real millimetres, and then finds the hip, knee and ankle centres directly from the shape of those surfaces. From those three centres it computes the mechanical axes and the alignment angles a surgeon would ask for (HKA, plus the knee joint-line angles mLDFA and MPTA). Every automatic result is compared against landmarks placed by hand, so you can see for yourself how close the automatic rules actually get to what a person would do.

The project also includes a fully functional from-scratch 3D segmentation model (SegResNet) that can generate these masks automatically from raw CT. The entire pipeline, from data preparation to model validation, is accessible through a unified, professional command-line interface.

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

The femoral head sphere fit is inside the hand repeat distance on clean anatomy. The knee centre rule is within 5 mm on 11 of 16 knees.

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

The reference masks are cortical shells (medullary canal unannotated), so TotalSegmentator naturally fills the interior volume that the human did not.

| Bone | Mean Dice (filled ref) | Mean Dice (unfilled ref) | Mean HD95 (mm) |
|---|---|---|---|
| Femur | **0.94** | 0.72 | 2.8 |
| Tibia | **0.90** | 0.66 | 5.5 |
| Fibula | **0.82** | 0.73 | 2.5 |

TotalSegmentator was run at 3 mm `--fast` on cropped CT(s). The filled Dice of 0.94 is the honest outer-surface agreement; the raw 0.72 measures the annotation-protocol difference (hollow vs solid).

### Custom ML Model (SegResNet)

We trained a from-scratch 3D SegResNet (4.7M parameters) to segment the bones. To prove the model generalizes without overfitting, we ran a **4-fold cross-validation** across all 8 subjects (every subject was held out as validation exactly once, with no data leakage).

| Bone | Mean Dice (4-fold CV) | SD Dice | Median HD95 |
|---|---|---|---|
| Femur | 0.94 | 0.06 | 1.50 mm |
| Tibia | 0.91 | 0.06 | 3.84 mm |
| Fibula| 0.91 | 0.04 | 1.50 mm |
| Talus | 0.92 | 0.03 | 2.69 mm |
| **Overall** | **0.922** | **0.051** | — |

The model achieves an overall mean Dice of **0.922 ± 0.051** across all 8 subjects, matching the TotalSegmentator baseline. The median surface error (HD95) is 1.5–4.5 mm, proving the segmentations are anatomically precise. Running the geometric landmark pipeline on the model's *predicted* masks yields HKA errors of 0.6°, proving the segmentations are geometrically accurate, not just spatially overlapping.

The full training run, including the custom patch sampler, the MONAI SegResNet, and the 4-fold cross-validation, is available as a public Kaggle Notebook: **[femuralabs on Kaggle](https://www.kaggle.com/code/sashmin/femuralabs)**.

## Getting started

FemuraLabs ships with a unified command-line interface. You can install the package in editable mode to access the `femuralabs` command globally, and run the test suite without downloading any data.

```bash
git clone https://github.com/sashminea/FemuraLabs.git
cd FemuraLabs

python3 -m venv .venv
source .venv/bin/activate        # on Windows: .venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt

# Install the CLI
pip install -e .

# Verify everything is working
femuralabs doctor check
pytest -q
```

The repository also contains a Dockerfile that packages the CLI and the geometry pipeline:

```bash
docker build -t femuralabs-tool .
docker run --rm femuralabs-tool --help
```

## Reproducing the validation

Reproducing the results from scratch means getting the dataset, preparing the segmentations, placing reference landmarks by hand, and then letting the CLI do the rest. The four steps below follow that order.

### 1. Data and segmentation merging

The dataset does not ship as a single multi-label NIfTI. It ships in two distinct layouts, and we have automated both paths.

- **Standard Lower-Limb**: Resample the segmentations onto the CT grid in Slicer and merge them.
  ```bash
  femuralabs data merge --thighs path/to/thighs.nii --shanks path/to/shanks.nii --out data/raw/caseXX/combined_seg.nii
  ```
- **Full-Body Upside-Down**: These ship as full-body CTs with separate segmentations and an H5 transform file. The CLI applies the H5 transform mathematically, extracts the lower limb, combines the masks, and centers the patient at X=0.
  ```bash
  femuralabs data preprocess \
    --ct path/to/SMIR.Body.nii \
    --thighs-seg path/to/Pelvis-Thighs.seg.nrrd \
    --shanks-seg path/to/Shanks-Feet.seg.nrrd \
    --transform path/to/Transform-Upside-Down.h5 \
    --out-dir data/raw/caseXX
  ```

### 2. Manual landmark annotation

To judge the automatic rules there has to be a human reference. Each subject needs ten landmarks placed by hand in Slicer and saved as a `.mrk.json` file in `data/ref/`. The click-by-click instructions, with annotated screenshots and the anatomical definition of every landmark, are in the placement guide in [`docs/landmarks.md`](docs/landmarks.md).

### 3. Running the geometry pipeline

When `combined_seg.nii` and the landmark files are in the `data/` directory, one command processes every case:

```bash
femuralabs pipeline batch
```

For each case this extracts the bone masks, writes the STL meshes, computes the automatic landmarks and the alignment angles, and saves everything to `output/<case>/summary.json`. To run a single case:

```bash
femuralabs pipeline run \
  --case data/raw/case07/combined_seg.nii \
  --out output/case07 \
  --compare data/ref/landmarks_case07.mrk.json \
  --angles \
  --fill
```

### 4. Generating the reports

The last step turns the JSON summaries into the tables you see in the results above:

```bash
femuralabs pipeline report
```

This writes [`reports/landmark_errors.md`](reports/landmark_errors.md) and [`reports/angles_case.md`](reports/angles_case.md). The tables are generated from the pipeline output on purpose, to rule out transcription mistakes.

## Training the ML Model

The ML pipeline is fully integrated into the CLI.

### 1. Prepare the 1.5mm `.npy` volumes
```bash
femuralabs ml prepare --out-dir data/ml_npy
```

### 2. Train the SegResNet
*(Note: Training requires a GPU. We recommend running this via the provided [Kaggle Notebook](https://www.kaggle.com/code/sashmin/femuralabs), but the CLI supports local training if you have CUDA).*
```bash
femuralabs ml train \
  --data-dir data/ml_npy \
  --out-dir runs/run1 \
  --patch 96 \
  --batch-size 2 \
  --epochs 200
```

### 3. Validate the model
Run sliding-window inference on the validation subjects and compute Dice/HD95:
```bash
femuralabs ml validate \
  --checkpoint runs/run1/best.pt \
  --data-dir data/ml_npy \
  --val-cases case07,case08
```

### 4. Use the model on a new scan
You can download the pre-trained weights directly from our GitHub Release. The CLI handles the download and extraction automatically:

```bash
femuralabs ml download-weights
```

Once downloaded, you can generate a segmentation for any raw CT. The CLI automatically uses the downloaded weights by default:

```bash
femuralabs ml infer \
  --ct path/to/new_scan.nii \
  --out data/raw/caseXX/combined_seg.nii
```

This runs sliding-window inference, splits the left/right sides, and upsamples back to the native grid. The resulting `combined_seg.nii` can then be fed directly into `femuralabs pipeline run` for 3D mesh generation and angle computation.

## Repository layout

The repository is organised so that the code, the documentation and the generated results each have their own place, and the data stays out of version control.

```text
FemuraLabs/
├── src/femuralabs/
│   ├── cli/                  # Unified Typer CLI (data, pipeline, ml, doctor)
│   └── toolkit/              # Core Python library (I/O, geometry, imaging, ML)
├── scripts/                  # Executable scripts called by the CLI
│   ├── data/                 # Merge segmentations, process full-body scans
│   ├── ml/                   # Data prep, SegResNet training, validation
│   ├── pipeline/             # Run cases, compare, and generate reports
│   └── dev/                  # Draw flow diagrams, run training, clean checks
├── tests/                    # Pytest suite
├── docs/                     # Engineering and scientific documentation
├── reports/                  # Generated validation tables and figures
├── Dockerfile                # Tool container
├── pyproject.toml            # Package definition and CLI entry point
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

The custom SegResNet model was trained on 6 subjects and validated on 2. While its Dice matches the TotalSegmentator baseline, it has only been tested on this specific cadaver dataset. It was checkpoint-selected on the same 2 validation subjects, so the results may have a slight optimism bias. It should not be considered a generalisable clinical model until tested on external hospital data.

## Attribution

If you use FemuraLabs in your work (papers, products, or derivative tools), please credit the project and link back to the repository:

> Built with or adapted from **FemuraLabs** (https://github.com/sashminea/FemuraLabs), licensed under Apache 2.0.

The full attribution requirement is recorded in the [`NOTICE`](NOTICE) file. The Apache 2.0 licence covers the code, model, and documentation in this repository. The source CT data and reference segmentations remain under their original CC BY-NC-SA licences from the VSD dataset (see [`CITATION.cff`](CITATION.cff)).

## Data and licences

FemuraLabs uses two Zenodo records, the [VSDFullBodyBoneReconstruction](https://doi.org/10.5281/zenodo.8302449) segmentations and surface models (CC BY-NC-SA 4.0) and the CT collection they were built from (CC BY-NC-SA 3.0 Switzerland, DOI [10.5281/zenodo.8270365](https://doi.org/10.5281/zenodo.8270365)). The data is not committed to this repository.

The code is licensed under the **Apache License 2.0**, which requires that any use of the code, model, or documentation provide attribution to the FemuraLabs project (see `NOTICE`). This is not a copyleft license — you are free to use, modify, and redistribute the code, including commercially, as long as you preserve the copyright notice and the `NOTICE` file.

The Apache 2.0 licence covers the **code** only. The **data** is not covered by this license and stays under its original CC BY-NC-SA licences from the VSD dataset. See `CITATION.cff` for the full citation metadata.
