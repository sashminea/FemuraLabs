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

Once the volume is loaded, each bone is pulled out of the combined segmentation as its own mask and turned into a triangle mesh with marching cubes. Each mesh is checked to make sure it is closed and that its volume agrees with the voxel volume of the mask, so a broken surface is caught here instead of three steps later as a strange angle.

The meshes are what the landmark rules work on, and there is one rule for each joint. The femoral head centre comes from fitting a sphere, by least squares, to the medial part of the top of the femur. The knee centre comes from splitting the bottom few millimetres of the femur into its two condyles and taking the midpoint between them. The ankle centre comes from finding the tibial plafond, which is the flat underside of the shin bone where it rests on the ankle, and taking the midpoint between the inner and outer ankle bones at that level. Each rule is written to mimic how a person would place the same point by hand.

With three centres per leg, the angles follow. HKA deviation is reported as positive for varus and negative for valgus, and the side of the body is detected automatically, so the same sign means the same thing on the left and the right leg. The joint-line angles mLDFA and MPTA are reported as acute angles (90° or less), which is how they are defined clinically, and the pipeline also computes the mechanical axis deviation in millimetres. Everything for a case is written to a JSON summary, and the report tables are generated from those summaries rather than typed in by hand, so the numbers in the report cannot drift away from the data.

## Results

To find out how well this works, the pipeline was run on three cadaveric subjects from the [VSDFullBodyBoneReconstruction](https://doi.org/10.5281/zenodo.8302449) dataset and compared with landmarks that were placed by hand in 3D Slicer. The first question is how far the automatic landmarks land from the hand-placed ones.

| Landmark | Average error, automatic vs. hand | Typical gap between two hand placements |
|---|---|---|
| Femoral head centre | 5.1 mm | 4 to 6 mm |
| Ankle centre | 3.9 mm | about 2 mm |
| Knee centre | 8.2 mm | 3 to 5 mm |

The averages cover both legs of all three subjects. The last column is there to put those errors in perspective, because a hand-placed landmark is not perfect either: the annotator placed several landmarks twice on the first subject, and the two placements of the same point differed by a few millimetres. A method that lands within that gap is about as consistent as a second person would be. These repeat gaps were measured on the first subject only, and the left ankle figure is an estimate rather than a measurement.

On that first subject the femoral head fit does exactly that, landing 3.8 and 4.8 mm from the hand reference on the right and left, against human gaps of 4.3 and 6.2 mm. The ankle rule is a little weaker, at roughly twice the human gap, mostly because the tibial plafond is used as a stand-in for the top of the talus. The knee rule is the least accurate of the three, and part of its error comes from the hand reference itself, which sits differently relative to the condyles on the left and right leg. The second subject was the hardest case overall, with femoral head and knee errors of around 8 to 10 mm.

What ultimately matters is whether the angles come out right, so the table below compares the angles computed from the automatic landmarks with the same angles computed from the hand-placed ones.

| Angle | Subjects | Average difference |
|---|---|---|
| HKA, right leg | 3 | 2.9° |
| HKA, left leg | 3 | 1.7° |
| mLDFA, right leg | 3 | 0.7° |
| MPTA, right leg | 3 | 0.4° |

To give those numbers some scale, the hand-placed HKA values across the three subjects run from mild valgus (about −4°) to clear varus (about +7°), and an 8 mm error in the knee centre on a thigh of typical length moves HKA by roughly one degree. The joint-line angles agree closely with the hand reference, though that comparison is limited by how noisy the hand-placed condyle and plateau points are (see the limitations below). The complete breakdown, including per-subject tables, is in [`reports/validation.md`](reports/validation.md), [`reports/landmark_errors.md`](reports/landmark_errors.md) and [`reports/angles_case.md`](reports/angles_case.md).

### Segmentation Comparison (TotalSegmentator)
To validate the reference masks themselves, we ran TotalSegmentator (a pre-trained neural network) on the CT volumes and compared its output to the human segmentations. Even on 3mm downsampled data, the agreement is strong:

| Bone | Mean Dice | Mean HD95 (mm) |
|---|---|---|
| Femur | 0.73 | 7.7 |
| Tibia | 0.67 | 5.5 |
| Fibula | 0.74 | 2.8 |

## Getting started

You can install the project and run its test suite without downloading any CT data, which is the quickest way to check that everything is set up properly on your machine.

```bash
git clone https://github.com/sashminea/FemuraLabs.git
cd FemuraLabs

python3 -m venv .venv
source .venv/bin/activate        # on Windows: .venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt

pytest -q                        # runs the 53 tests
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

The pipeline reads a single multi-label NIfTI file called `combined_seg.nii`, in which every bone has its own label: `femur_R`, `femur_L`, `tibia_R`, `tibia_L`, `fibula_R`, `fibula_L`, `talus_R` and `talus_L`. The dataset does not ship that way. The femur and tibia segmentations come as separate files on cropped volumes, so they first have to be resampled onto the full-limb CT grid in 3D Slicer, exported, and then merged. The exact Slicer steps, with the settings that matter, are in [`docs/runbook.md`](docs/runbook.md) under "Combining the two reference segmentations". The merge itself is done by `scripts/merge_segmentation.py`, which reads Slicer's `.labels.csv` files and maps source labels by name, so a subject whose labels arrive in a different order cannot silently end up with the wrong bone under the wrong label.

Not every subject has a single full-limb CT. Some are split into a pelvis-and-thighs volume and a shanks-and-feet volume, and the tempting shortcut of stacking the two halves in Python truncates the bones, because the volumes are cropped independently. The dataset authors provide an MRML scene file that loads the unified volume correctly in Slicer, and that is the route to use. [`docs/data.md`](docs/data.md) describes the datasets, their licences, the label mappings, and this split-volume case in detail.

### 2. Manual landmark annotation

To judge the automatic rules there has to be a human reference to compare them with, so each subject needs ten landmarks placed by hand in Slicer and saved as a `.mrk.json` file in `data/ref/`. The click-by-click instructions, with annotated screenshots and the anatomical definition of every landmark, are in the placement guide in [`docs/landmarks.md`](docs/landmarks.md). Please read the section on pitfalls in that file before you place anything. The most important one is that Slicer's axial view follows radiological convention, so the patient's right side appears on the left of the screen, and labelling by screen position produces a perfectly plausible but completely mirrored result.

Once the file is saved, run the diagnostic scripts in the appendix of [`docs/runbook.md`](docs/runbook.md). They confirm that right-side landmarks have negative x and left-side landmarks positive x in LPS, and that the points actually rest on the bone masks.

### 3. Running the pipeline

When `combined_seg.nii` and the landmark files are in the `data/` directory, one command processes every case:

```bash
PYTHONPATH=src python scripts/run_all_cases.py
```

For each case this extracts the bone masks, writes the STL meshes, computes the automatic landmarks and the alignment angles, and saves everything to `output/<case>/summary.json`. Bones are meshed one at a time and memory is released in between, which keeps the peak at about 3 GB even on the largest scan (512 × 512 × 1969 voxels) instead of running out of memory on a standard laptop. If you only want to process a single case, [`docs/runbook.md`](docs/runbook.md) explains how under "Running the pipeline on one case".

### 4. Generating the reports

The last step turns the JSON summaries into the tables you see in the results above:

```bash
python scripts/make_report_tables.py
```

This writes [`reports/landmark_errors.md`](reports/landmark_errors.md) and [`reports/angles_case.md`](reports/angles_case.md). The tables are generated from the pipeline output on purpose, to rule out transcription mistakes, but it also means they can go stale: after any run that changes a result, run this script again. More detail is in the runbook under "Generating the reports".

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
│   ├── data/                 # Merge segmentations, crop for TotalSegmentator
│   ├── pipeline/             # Run cases, compare, and generate reports
│   └── dev/                  # Draw flow diagrams, run training, clean checks
├── tests/                    # Pytest suite (62 tests)
│   ├── core/                 # Tests for general utilities and the CLI
│   ├── pipeline/             # Tests for geometry, metrics, and alignment
│   ├── service/              # Tests for the HTTP API
│   └── training/             # Tests for the PyTorch utilities
├── docs/                     # Engineering and scientific documentation
│   ├── runbook.md            # Exact commands and diagnostic scripts
│   ├── landmarks.md          # Placement guides and algorithm rules
│   ├── data.md               # Dataset, licensing, and merge procedures
│   └── decisions.md          # Architectural design choices (D001-D042)
├── reports/                  # Generated validation tables and figures
│   ├── validation.md         # Main results report
│   └── angles_case.md        # Auto-generated angle comparisons
├── Dockerfile                # CPU-only tool container (synthetic demo)
├── requirements.txt          # Dev environment (torch, numpy, etc.)
└── CITATION.cff              # Dataset, paper, and tool references
```

## Documentation

Most of the detail that does not fit in a README lives in `docs/`, and each file is written to be read on its own.

- [`reports/validation.md`](reports/validation.md) is the full validation report, with the method limitations and the angle error tables.
- [`docs/runbook.md`](docs/runbook.md) lists every command, Slicer workflow and diagnostic script, along with the output you should expect to see.
- [`docs/landmarks.md`](docs/landmarks.md) covers the coordinate traps, the click-by-click placement guide, the hand-placement repeat distances and the rules behind the automatic landmarks.
- [`docs/conventions.md`](docs/conventions.md) defines the coordinate frame (LPS and RAS), the anatomical definition of each landmark and the sign convention for the angles.
- [`docs/data.md`](docs/data.md) describes the datasets, their licences, the label mappings and how to handle split-volume subjects.
- [`docs/decisions.md`](docs/decisions.md) records the design choices (D001 to D039) together with the alternatives that were rejected and why.
- [`docs/architecture.md`](docs/architecture.md) is the folder map and a description of the pipeline stages.
- [`docs/FLOW.md`](docs/FLOW.md) holds annotated call graphs showing how data moves between modules.
- `AGENTS.md` sets out the rules for AI agents and contributors, and `CITATION.cff` has the citation details for the dataset, the paper and the tools.

## Limitations

It is worth being clear about what this project does not claim. It has been evaluated on three cadaveric subjects, which is far too few for statistical conclusions, so the results are descriptive and should be read as a proof of concept. The scans are post-mortem and supine, which means the geometry does not match a standing, weight-bearing patient, and all hand-placed landmarks come from a single annotator.

The hand reference is also the weakest link in places. The condyle and plateau points used for the joint-line angles were placed by clicking on a surface, and those clicks repeat only to within 7 to 9 mm, against 2 to 3 mm for landmarks defined as the midpoint of two clear anatomical features. That noise limits how finely mLDFA and MPTA can be validated, and left-side joint-line landmarks were not placed for the second and third subjects at all. Near-neutral legs are also where small landmark errors matter most: on the second subject's right leg the automatic HKA is +3.5° while the hand value is −1.4°, which flips the label from varus to valgus.

On the method side, the ankle rule uses the tibial plafond as a stand-in for the talar dome. The talus is already segmented and merged into `combined_seg.nii`, but the rule does not use it yet, and the documentation names the condition under which that should change. The most natural ways to strengthen the project are more subjects, an annotation pass with more than one person, and measured repeat distances for every landmark on every subject.

The TotalSegmentator comparison was run on 3mm downsampled CTs using a bounding-box crop, because the full-resolution model requires more than 16 GB of RAM. This introduces a 3mm boundary error; future work on a workstation with more memory should use the native 1.5mm model.

## Data and licences

FemuraLabs uses two Zenodo records, the [VSDFullBodyBoneReconstruction](https://doi.org/10.5281/zenodo.8302449) segmentations and surface models (CC BY-NC-SA 4.0) and the CT collection they were built from (CC BY-NC-SA 3.0 Switzerland, DOI [10.5281/zenodo.8270365](https://doi.org/10.5281/zenodo.8270365)). The data is not committed to this repository. The code is MIT-licensed, but the MIT licence does not cover the data, which stays under its own licences. If you use this work, please cite it with the details in `CITATION.cff`.
