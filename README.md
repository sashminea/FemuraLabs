# FemuraLabs

A research prototype for lower-limb CT analysis: segment femur and tibia
from CT, build 3D meshes, place anatomical landmarks, and compute
mechanical axes and alignment angles.

<img width="2873" height="852" alt="Frame 3" src="https://github.com/user-attachments/assets/4c9b2855-fa56-49c3-8333-5c490fe793d4" />


## What it does (eventually)

- Read and preprocess DICOM and NIfTI volumes with correct geometry
- Segment femur and tibia from lower-limb CT
- Reconstruct 3D bone meshes and export STL
- Detect hip, knee and ankle landmarks
- Compute mechanical axes and alignment angles (HKA, mLDFA, MPTA)
- Simulate a simple osteotomy wedge
- Produce a validation report with all measurements

Right now it contains the Day 1 foundation: a tested array toolkit for
summarising `.npy` arrays, per-volume z-score normalisation, a linear
intensity window, and a slow reference 2D convolution.

## Quick start

```bash
git clone git@github.com:sashminea/FemuraLabs.git
cd FemuraLabs

python3 -m venv .venv
source .venv/bin/activate          # WSL/Linux
# OR: .venv\Scripts\Activate.ps1    # Windows PowerShell

pip install -r requirements.txt

# run the tests
pytest -q

# run the array summary tool on a saved array
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

## Layout

```
femuralabs/
├── src/femuralabs/       # importable code
│   └── toolkit/          # array helpers, summary tool
├── tests/                # pytest tests
├── notebooks/            # exploration only
├── data/                 # local data, never committed
├── reports/              # figures and hand-work photographs
├── docs/                 # logs, notes, conventions
└── requirements.txt
```

## Limits

Learning prototype. Not for clinical use. No patient data is included
or ever committed. Nothing in this repository is a medical device or
a substitute for clinical judgement.
