# Architecture

## Layout

    src/femuralabs/toolkit/     importable package
      arrays.py                 NumPy helpers (zscore, window, conv2d)
      summary.py                statistics of a .npy file, and a CLI
      volume_info.py            make_volume, describe
      cli.py                    volume geometry CLI
      io.py                     save_json primitive
      report.py                 write_info: JSON report writer
      decision.py               verdict rule for repeated runs
      training/                 model.py, train_utils.py
      service/                  routes.py, api.py, serve.py (HTTP)

    scripts/                    one-off scripts, run by hand
    tests/                      pytest suite
    docs/                       documentation (see AGENTS.md)
    web/                        static page served by the `web` Compose service

    Dockerfile                  tool image (numpy, non-root `student`)
    docker-compose.yml          `api` (built) + `web` (public image)
    requirements.txt            dev environment (torch, numpy, matplotlib, pytest)
    requirements-tool.txt       tool image only (numpy, pinned)

## Data pipeline (planned)

    Input volume (NRRD/NIfTI)
      -> load_volume (SimpleITK), write NIfTI          [io_volume.py]
      -> extract femur/tibia masks                     [masks.py]
      -> mesh per bone (marching cubes, mm)            [mesh.py]
      -> landmarks (hip, knee, ankle)                  [landmarks.py  - pending]
      -> alignment angles (HKA, mLDFA, MPTA)           [alignment.py  - pending]
      -> comparison with TotalSegmentator              [metrics.py    - pending]
      -> validation report                             [reports/validation.md]

`pending` means not yet written. See `docs/decisions.md` D025 and the
sprint plan for what triggers each file.

## Existing pipeline (no data required)

    synthetic volume
      -> make_volume (zeros) -> describe -> CLI prints geometry
      -> write_info -> save_json -> info.json
      -> HTTP service: /health, /info (reads REPORT_FOLDER/info.json if present)
    
    combined_seg.nii (labels 1=ferur_R, 2=femur_L, 3=tibia_R, 4=tibia_L)
      -> load_volume -> Volume(array, spacing, origin, direction)
      -> save_nifti -> round trip preserves geometry
      -> extract_masks -> BoneMask per bone (mask, count, mL, centroid_world)

## Where each fact lives

- **How to run a stage**: `docs/runbook.md`
- **Why a design looks unusual**: `docs/decisions.md`
- **What the data is, licence, coverage**: `docs/data.md`
- **Citations**: `CITATION.cff`
- **Rules for agents and contributors**: `AGENTS.md`
- **Call graphs at each stage**: `docs/FLOW.md`