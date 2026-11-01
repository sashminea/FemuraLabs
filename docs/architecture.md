# Architecture

## Layout

    src/femuralabs/toolkit/     importable package
      fileio/
        json_utils.py           save_json primitive
        volume.py               load_volume, save_nifti (SimpleITK)
        landmark.py             load_landmarks (.mrk.json), repeat_distances
      imaging/
        arrays.py               NumPy helpers (zscore, window, conv2d)
        masks.py                extract_masks, BoneMask, LABEL_NAMES
        mesh.py                 mask_to_mesh, save_stl, signed_volume, edge_incidence
        volume_info.py          make_volume, describe
      geometry/
        landmarks.py            femoral_head_centre, knee_centre, ankle_centre
        alignment.py            hka_deviation, mad, mldfa, mpta
        metrics.py              dice_score, hd95 (KDTree implementation)
        stats.py                confidence_interval, bland_altman
      reporting/
        decision.py             verdict rule for repeated runs
        report.py               write_info (JSON report writer)
        summary.py              statistics of a .npy file, and a CLI
      service/                  routes.py, api.py, serve.py (HTTP)
      training/                 model.py, train_utils.py (PyTorch)
      cli.py                    volume geometry CLI

    scripts/
      data/                     merge_segmentation.py, totalseg_bbox_crop.py, paste_back.py
      pipeline/                 pipeline_demo.py, run_all_cases.py, compare_segmentations.py
      dev/                      draw_flow.py, clean_check.sh, train_small_cnn.py

    tests/
      core/                     test_cli.py, test_report.py, test_arrays.py, test_decision.py
      pipeline/                 test_landmarks.py, test_alignment.py, test_mesh.py, etc.
      service/                  test_routes.py
      training/                 test_train_utils.py

    docs/                       documentation (see AGENTS.md)
    web/                        static page served by the `web` Compose service

    Dockerfile                  tool image (numpy, SimpleITK, scikit-image, non-root `student`)
    docker-compose.yml          `api` (built) + `web` (public image)

## Data pipeline (planned)

    Input volume (NRRD/NIfTI)
      -> load_volume (SimpleITK), write NIfTI          [io_volume.py]
      -> extract femur/tibia/fibula/talus masks                     [masks.py]
      -> mesh per bone (marching cubes, mm)            [mesh.py]
      -> mesh verification (watertight, volume)        [mesh.py]      
      -> landmarks (hip, knee, ankle)                  [landmarks.py]
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