# Docker chapter (1.4) — adaptations to FemuraLabs

The chapter uses toy names (`toolkit`, `hello_pipeline`, `requirements.txt`).
Where FemuraLabs already has a different name, we keep the existing one.

| Chapter says | FemuraLabs does | Why |
|---|---|---|
| `requirements.txt` holds pinned numpy | separate `requirements-tool.txt` | root `requirements.txt` pulls the CUDA torch wheel (GB); the tool container needs numpy only |
| package `toolkit` | package `femuralabs.toolkit` | existing package name |
| Block 3.2 tool prints shape/spacing/dtype/extent | new `femuralabs.toolkit.cli` | different question from `summary.py` (geometry vs statistics); does not touch the tested `summary` output |
| `hello_pipeline.py` self-contained | imports `make_volume` from `femuralabs.toolkit.volume_info` | one implementation of `make_volume` |
| `.dockerignore` from Block 3.5 | introduced at Block 1.3, before first build | without it, `.venv` (with torch) is shipped to the builder on every build |
| — | `docs/`, `tests/`, `notebooks/` also in `.dockerignore` | not needed inside the image; small but tidy |

## Known pre-existing issues (not fixed by this chapter)
- `runs/`, `reports/`, `notebooks/*.ipynb` are tracked in git. Training-chapter cleanup.