# Runbook

Every command below was typed and worked on this workstation.
Append a block when a stage is verified; delete a block if it breaks.

## Every session
    cd ~/FemuraLabs
    source .venv/bin/activate
    pwd && which python && git status

## Tests
    pytest -q
    # expected: 7 passed

## Statistics summary tool (existing)
    mkdir -p data
    python -c 'import numpy as np; np.save("data/small.npy", np.arange(6, dtype=np.float32).reshape(2,3))'
    PYTHONPATH=src python -m femuralabs.toolkit.summary data/small.npy
    # expected: shape (2, 3) / dtype: float32 / min 0.00 / max 5.00 / mean 2.50

## Tool image (Blocks 1.3–1.4)
    docker build -t toolkit-hello .
    docker run --rm toolkit-hello
    # expected: shape (z, y, x): (4, 6, 6) / spacing (mm): (2.0, 1.0, 1.0) / dtype: float32

## Clean checkout (Objective 1)
    cd /tmp && rm -rf scratch_check
    git clone ~/FemuraLabs scratch_check
    cd scratch_check
    docker build -t toolkit-hello-clean .
    docker run --rm toolkit-hello-clean
    cd ~/FemuraLabs