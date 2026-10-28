# FemuraLabs

A research prototype for lower-limb CT analysis: segment femur and tibia
from CT, build 3D meshes, place anatomical landmarks, and compute
mechanical axes and alignment angles. Development uses the public
**VSDFullBodyBoneReconstruction** dataset (segmentations and surface models
of pelvis and lower-limb bones, made from a public postmortem CT collection;
see `docs/data.md`). No patient data is included or required.

<img width="2873" height="852" alt="FemuraLabs Banner" src="https://github.com/user-attachments/assets/41d18b7f-2fb5-4f52-b184-500358c6faa7" />

## What it does (eventually)

- Read and preprocess DICOM and NIfTI volumes with correct geometry
- Segment femur and tibia from lower-limb CT
- Reconstruct 3D bone meshes and export STL
- Detect hip, knee and ankle landmarks
- Compute mechanical axes and alignment angles (HKA, mLDFA, MPTA)
- Simulate a simple osteotomy wedge
- Produce a validation report

Right now it contains five pieces of foundation:

- **Array toolkit.** NumPy helpers for holding images in arrays: a `.npy`
  summary CLI, per-volume z-score normalisation, a linear Hounsfield-unit
  intensity window, and a reference 2D convolution checked against a
  hand-worked Sobel result.
- **Training pipeline.** A small CNN and a complete PyTorch training loop
  with seeded reproducibility, per-epoch CSV logging, best-checkpoint
  saving, and plotted learning curves. Every run writes `config.json`
  (with seed and git commit hash), `environment.json`, `metrics.csv`, and
  the best checkpoint.
- **Verdict rule.** `femuralabs.toolkit.decision.verdict` turns two lists
  of per-seed scores and a threshold into
  `supported` / `inconclusive` / `not supported` by comparing the interval
  `d ± 2s` with the threshold.
- **Container and service.** A `Dockerfile` that runs the geometry tool as
  a non-root user on CPU, and a `docker-compose.yml` that starts an HTTP
  service and a static page together on one private network. Data mounted
  read-only, results writable, image holds neither folder.
- **CT pipeline.** `scripts/pipeline_demo.py` runs the whole chain on one
  case: load a combined segmentation, extract per-bone masks, build a
  triangle mesh per bone, write four STLs and a JSON summary. Deterministic
  (same input, same JSON); the four labelled bones are femur_R, femur_L,
  tibia_R, tibia_L with volumes in mL and centroids in millimetres.

## Quick start

    git clone git@github.com:sashminea/FemuraLabs.git
    cd FemuraLabs

    python3 -m venv .venv
    source .venv/bin/activate          # WSL/Linux
    # OR: .venv\Scripts\Activate.ps1    # Windows PowerShell

    python -m pip install --upgrade pip
    pip install -r requirements.txt

`torch` installs from the CUDA wheel index by default. On a machine with
no NVIDIA GPU, replace the torch line in `requirements.txt` with the CPU
build from https://pytorch.org/get-started/locally and reinstall.

### The four things to try first

    # 1. Tests
    pytest -q

    # 2. The tool in a container — prints a synthetic volume's geometry
    docker build -t toolkit-hello . && docker run --rm toolkit-hello

    # 3. Both services on one network — api on :8000, web on :8080
    docker compose up --build -d
    curl http://localhost:8000/health
    docker compose down

    # 4. The pipeline on one case — writes four STLs and summary.json
    PYTHONPATH=src python scripts/pipeline_demo.py \
      --case data/raw/case01/combined_seg.nii --out output/case01

The full list of commands — mounting data in and results out, summarising a
saved `.npy`, training the small CNN, comparing two runs — is in
`docs/runbook.md`, with expected output and failure modes.

## Documentation

- `docs/runbook.md` — every command that has been run, with expected
  output and failure modes including the CT pipeline, mesh verification, and the data merge.
- `docs/decisions.md` — architectural choices, with the alternative
  rejected and the reason.
- `docs/architecture.md` — folder map and pipeline stages.
- `docs/data.md` — dataset, licence, coverage, how the two reference
  segmentations are combined.
- `docs/FLOW.md` — cumulative annotated call graphs, newest first.
- `AGENTS.md` — rules for AI agents and contributors.
- `CITATION.cff` — citations for dataset, paper, tools.
- `LICENSE` — MIT for the code; data has its own licences (below).

## Reproducibility

Seeds are fixed for Python, NumPy and PyTorch, including CUDA. The
train/validation split uses a seeded generator, so it is identical on every
run. Every training run writes a folder under `runs/` containing
`config.json`, `environment.json`, `metrics.csv`, and the best checkpoint.

Repeating a run with the same seed produces a validation loss that differs
by `0.00e+00` on CPU (and by a value in the fifth or sixth decimal on GPU,
where floating-point addition order differs between kernels).
`scripts/compare_runs.py` reports the largest gap;
`femuralabs.toolkit.decision.verdict` turns repeated-seed scores into a
three-way verdict.

## Data and tools

Uses [VSDFullBodyBoneReconstruction](https://doi.org/10.5281/zenodo.8302449)
(CC BY-NC-SA 4.0) and its source CT collection (CC BY-NC-SA 3.0 CH). Data
are not committed. See `docs/data.md` for coverage and `CITATION.cff` for
citations.

Built with 3D Slicer, SimpleITK, scikit-image, and TotalSegmentator
(academic licence). Tool citations are in `CITATION.cff`.

## Licence

Code is MIT-licensed (see `LICENSE`). Data uses are governed by their own
licences (see `docs/data.md`); the MIT licence does not cover the data.
