# FemuraLabs

A research prototype for lower-limb CT analysis: segment femur and tibia
from CT, build 3D meshes, place anatomical landmarks, and compute
mechanical axes and alignment angles.

<img width="2873" height="852" alt="FemuraLabs Banner" src="https://github.com/user-attachments/assets/41d18b7f-2fb5-4f52-b184-500358c6faa7" />

## What it does (eventually)

- Read and preprocess DICOM and NIfTI volumes with correct geometry
- Segment femur and tibia from lower-limb CT
- Reconstruct 3D bone meshes and export STL
- Detect hip, knee and ankle landmarks
- Compute mechanical axes and alignment angles (HKA, mLDFA, MPTA)
- Simulate a simple osteotomy wedge
- Produce a validation report with all measurements

Right now it contains two pieces of foundation:

**Array toolkit.** A tested set of helpers for holding images in NumPy
arrays: a `.npy` summary command-line tool, per-volume z-score
normalisation, a linear Hounsfield unit intensity window, and a slow
reference 2D convolution that matches a hand-worked Sobel result. 

**Training pipeline.** — A small convolutional network and a complete
PyTorch training loop with seeded randomness, per-epoch CSV logging,
best-checkpoint saving by validation loss, and plotted learning curves.
Two runs with the same seed produce nearly identical numbers.

**Container and service** — a `Dockerfile` that runs the geometry tool as a non-root user on CPU only, and a `docker-compose.yml` that starts an HTTP service and a static page together on one private network. Data is mounted read-only, results are mounted writable, the image holds neither folder.


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

### The three things to try first

    # 1. Tests — 16 pass, covering arrays, training utils, routes, CLI, report
    pytest -q

    # 2. The tool in a container — prints a synthetic volume's geometry
    docker build -t toolkit-hello . && docker run --rm toolkit-hello

    # 3. Both services on one network — api on :8000, web on :8080
    docker compose up --build -d
    curl http://localhost:8000/health
    docker compose down

The full list of commands — mounting data in and results out, summarising
a saved `.npy`, training the small CNN, comparing two runs — is in
`docs/RUNBOOK.md`, with expected output and failure modes.

## Layout

    src/femuralabs/toolkit/
      arrays.py     summary.py     volume_info.py
      cli.py        io.py          report.py
      training/     model.py       train_utils.py
      service/      routes.py      api.py      serve.py

    scripts/        run-by-hand entry points:
                    hello_pipeline.py, train_small_cnn.py, compare_runs.py,
                    api_demo.py, check_tree.py, clean_check.sh, draw_flow.py
    tests/          pytest suite (16 tests across 5 files)
    web/            static page served by the `web` service
    docs/           INVENTORY, DECISIONS, RUNBOOK, FLOW, flow/ (PNG diagrams)
    AGENTS.md       working protocol and constraints for agents and contributors

    Dockerfile                tool image (numpy only, non-root student)
    docker-compose.yml        api + web on one private network
    requirements.txt          dev env (torch, numpy, matplotlib, pytest)
    requirements-tool.txt     tool image only (numpy, pinned)
    data/, output/, runs/     not committed

## Documentation

Maintainer detail lives in `docs/`:

- `docs/RUNBOOK.md` — every command that has been run, with expected output
  and failure modes.
- `docs/DECISIONS.md` — every design choice, with the alternative that was
  rejected and why.
- `docs/INVENTORY.md` — every tracked path, one row per file.
- `docs/FLOW.md` — annotated call graphs, cumulative.
- `AGENTS.md` — working protocol, constraints, documentation rules.

## Reproducibility

Seeds are fixed for Python, NumPy and PyTorch, including CUDA. The
train/validation split uses a seeded generator, so it is identical on
every run. Every run writes `config.json`, `metrics.csv` and the best
checkpoint into its own folder under `runs/`. Repeating a run with the
same seed produces a validation loss that differs by `0.00e+00` on CPU
(and by a value in the fifth or sixth decimal on GPU, where floating
point addition order differs between kernels). `scripts/compare_runs.py`
reports the largest gap.
