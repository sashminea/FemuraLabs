# Project inventory

Every tracked file, its kind, its inputs → outputs, and where it came from.
Kept accurate by `scripts/check_tree.py` (run before every commit).

Kinds: **module** = importable, returns values, prints nothing; **script** = run by hand;
**config** = read by a tool; **docs** = prose; **run output** = produced by a script.

| Path | Kind | In → out | Introduced |
|---|---|---|---|
| `.dockerignore` | config | — | Block 1.3 |
| `.gitignore` | config | — | pre-docker |
| `Dockerfile` | config | project files → image | Block 1.3 |
| `README.md` | docs | — | pre-docker |
| `conftest.py` | config | makes `src/` importable for pytest | pre-docker |
| `data/.gitkeep` | placeholder | — | pre-docker |
| `docs/INVENTORY.md` | docs | — | this block |
| `docs/docker_adaptations.md` | docs | — | this block |
| `docs/RUNBOOK.md` | docs | — | this block |
| `notebooks/01_numpy_images.ipynb` | notebook | — | pre-docker |
| `notebooks/02_pytorch_loop.ipynb` | notebook | — | pre-docker |
| `reports/*.png`, `reports/*.jpg` | figures | — | pre-docker |
| `requirements-tool.txt` | config | numpy pin for the tool image | Block 1.3 |
| `requirements.txt` | config | full env (incl. torch CUDA) | pre-docker |
| `runs/run_a/*`, `runs/run_b/*` | run output | — | pre-docker |
| `scripts/check_tree.py` | script | tree → ok/MISSING lines | this block |
| `scripts/compare_runs.py` | script | two `metrics.csv` → max diff | pre-docker |
| `scripts/hello_pipeline.py` | script | — → 3 printed lines | Block 1.2 |
| `scripts/train_small_cnn.py` | script | flags → `runs/`, `reports/` | pre-docker |
| `src/femuralabs/__init__.py` | package marker | — | pre-docker |
| `src/femuralabs/toolkit/__init__.py` | package marker | — | pre-docker |
| `src/femuralabs/toolkit/arrays.py` | module | array → array (zscore, window, conv2d) | pre-docker |
| `src/femuralabs/toolkit/model.py` | module | tensor batch → logits | pre-docker |
| `src/femuralabs/toolkit/summary.py` | module | `.npy` path → `ArraySummary` | pre-docker |
| `src/femuralabs/toolkit/train_utils.py` | module | training building blocks | pre-docker |
| `tests/test_arrays.py` | test | — → pass/fail | pre-docker |
| `tests/test_train_utils.py` | test | — → pass/fail | pre-docker |