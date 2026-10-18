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

**Training pipeline.** A small convolutional network and a complete
PyTorch training loop with seeded randomness, per-epoch CSV logging,
best-checkpoint saving by validation loss, and plotted learning curves.
Two runs with the same seed produce nearly identical numbers.

## Quick start

```bash
git clone git@github.com:sashminea/FemuraLabs.git
cd FemuraLabs

python3 -m venv .venv
source .venv/bin/activate          # WSL/Linux
# OR: .venv\Scripts\Activate.ps1    # Windows PowerShell

python -m pip install --upgrade pip
python -m pip install --upgrade pip
pip install -r requirements.txt
```

`torch` is installed from the CUDA wheel index by default. On a machine
with no NVIDIA GPU, replace the torch line in `requirements.txt` with the
CPU build from https://pytorch.org/get-started/locally and reinstall.
The training script selects the device automatically.


### Run the tests

```bash
pytest -q
```

Expected: all tests pass. This covers the array helpers (z-score,
window, convolution) and the training utilities (seeding, checkpoint
round trip).

### Run the hello script in a container

The tool image needs NumPy only, so it uses `requirements-tool.txt`
rather than the training requirements.
```
    docker build -t toolkit-hello .
    docker run --rm toolkit-hello
```


Expected output:
```
    shape (z, y, x): (4, 6, 6)
    spacing (mm): (2.0, 1.0, 1.0)
    dtype: float32
```


### Summarise a saved array

Create a small `.npy` file to test with:

```bash
mkdir -p data
python -c "import numpy as np; np.save('data/small.npy', np.arange(6, dtype=np.float32).reshape(2, 3))"
PYTHONPATH=src python -m femuralabs.toolkit.summary data/small.npy
```

Expected output:

```
shape: (2, 3)
dtype: float32
min: 0.00
max: 5.00
mean: 2.50
```

### Train the small CNN

The training script downloads MNIST into `data/` on first run. Each run
gets its own folder under `runs/`, containing `config.json`,
`metrics.csv`, and `best.pt` (the best checkpoint by validation loss).
The learning curves are written to `reports/`.

```bash
PYTHONPATH=src python scripts/train_small_cnn.py \
    --seed 0 --epochs 5 --run-name run_a
```

Expected output: one line per epoch with training loss, validation loss,
and accuracy, then a PNG in `reports/run_a_curves.png`.

### Verify reproducibility

Run the same command again under a different run name and compare:

```bash
PYTHONPATH=src python scripts/train_small_cnn.py \
    --seed 0 --epochs 5 --run-name run_b

PYTHONPATH=src python scripts/compare_runs.py \
    runs/run_a/metrics.csv runs/run_b/metrics.csv
```

Expected: `max difference in val_loss` of `0.00e+00` on CPU, or a value
in the fifth or sixth decimal on GPU (floating-point addition order
differs between CUDA kernels). A difference in the first decimal means
a random source is not seeded.
=======

## Layout

```
femuralabs/
├── conftest.py                 # makes src/ importable during tests
├── src/femuralabs/
│   └── toolkit/
│       ├── arrays.py           # zscore_batch, window_to_uint8, conv2d
│       ├── model.py            # SmallCNN (9098 parameters)
│       ├── summary.py          # command-line .npy summary tool
│       └── train_utils.py      # seeding, device, checkpoints, logging, curves
├── scripts/
│   ├── train_small_cnn.py      # training entry point
│   ├── compare_runs.py         # compare two runs' metrics
│   └── scratch_*.py            # exploration only
├── tests/                      # pytest suite
├── notebooks/                  # exploration only
├── data/                       # local data, never committed
├── runs/                       # per-run config, metrics, checkpoint (ignored)
├── reports/                    # saved figures
├── docs/                       # logs, notes, conventions
├── conftest.py                 # makes src/ importable during tests
├── src/femuralabs/
│   └── toolkit/
│       ├── arrays.py           # zscore_batch, window_to_uint8, conv2d
│       ├── model.py            # SmallCNN (9098 parameters)
│       ├── summary.py          # command-line .npy summary tool
│       └── train_utils.py      # seeding, device, checkpoints, logging, curves
├── scripts/
│   ├── train_small_cnn.py      # training entry point
│   ├── compare_runs.py         # compare two runs' metrics
│   └── scratch_*.py            # exploration only
├── tests/                      # pytest suite
├── notebooks/                  # exploration only
├── data/                       # local data, never committed
├── runs/                       # per-run config, metrics, checkpoint (ignored)
├── reports/                    # saved figures
├── docs/                       # logs, notes, conventions
└── requirements.txt
```

## Reproducibility

- Seeds are fixed for Python, NumPy, and PyTorch, including CUDA.
- The train/validation split uses a seeded generator, so it is identical
  on every run.
- Every run folder stores its command-line settings in `config.json`,
  its per-epoch numbers in `metrics.csv`, and the best checkpoint in
  `best.pt`.
- A repeated run with the same seed and different run name should produce
  nearly identical validation losses. `scripts/compare_runs.py` reports
  the largest gap.
