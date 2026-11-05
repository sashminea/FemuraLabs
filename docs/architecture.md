# Architecture

## Layout

    src/femuralabs/toolkit/     importable package
      fileio/
        json_utils.py           save_json primitive
        volume.py               load_volume, save_nifti (SimpleITK)
        landmark.py             load_landmarks (.mrk.json), repeat_distances
      imaging/
        arrays.py               NumPy helpers (zscore, window, conv2d)
        masks.py                extract_masks, BoneMask, LABEL_NAMES (8 labels)
        mesh.py                 mask_to_mesh, save_stl, signed_volume, edge_incidence
        volume_info.py          make_volume, describe
      geometry/
        landmarks.py            femoral_head_centre, knee_centre, ankle_centre
        alignment.py            hka_deviation, mad, mldfa, mpta
        metrics.py              dice_score, hd95 (KDTree surface distances)
        stats.py                confidence_interval, bland_altman
      reporting/
        decision.py             verdict rule for repeated runs
        report.py               write_info (JSON report writer)
        summary.py              statistics of a .npy file, and a CLI
      service/                  routes.py, api.py, serve.py (HTTP)
      training/                 model.py, train_utils.py (PyTorch)
      cli.py                    volume geometry CLI

    scripts/
      data/                     merge_segmentation.py, process_full_body_raw.py,
                                paste_back.py, totalseg_bbox_crop.py,
                                fix_upside_down_geometry.py
      pipeline/                 pipeline_demo.py, run_all_cases.py,
                                compare_segmentations.py, make_report_tables.py,
                                calculate_agreement.py, demo_synthetic.py
      dev/                      draw_flow.py, clean_check.sh, train_small_cnn.py,
                                inventory_dataset.py, hello_pipeline.py,
                                api_demo.py, compare_runs.py

    tests/
      core/                     test_cli.py, test_report.py, test_arrays.py, test_decision.py
      pipeline/                 test_landmarks.py, test_alignment.py, test_mesh.py,
                                test_io_volume.py, test_masks.py, test_landmark_io.py,
                                test_metrics.py, test_stats.py, test_pipeline_demo.py
      service/                  test_routes.py
      training/                 test_train_utils.py

    docs/                       documentation (see AGENTS.md)
    web/                        static page served by the `web` Compose service

    Dockerfile                  tool image (numpy, SimpleITK, scikit-image, non-root `student`)
    docker-compose.yml          `api` (built) + `web` (public image)
    pytest.ini                  redirects tmp_path to /dev/shm to avoid C: drive bloat

## Data pipeline

Two input layouts are supported. Both converge on a single `combined_seg.nii`
with 8 fixed labels, after which the pipeline is identical.

### Layout A: Standard lower-limb (case01–case03)

    Input volume (SMIR.Lower_limb...nrrd)
      -> load with Slicer, apply Segment Geometry to full-limb grid
      -> export thighs and shanks segmentations as NIfTI
      -> merge_segmentation.py (CSV-driven label mapping)
      -> combined_seg.nii (8 labels, native CT grid)

### Layout B: Full-body upside-down (case04–case08)

    Input volume (SMIR.Body...nii) + Transform-Upside-Down.h5
      -> process_full_body_raw.py
         1. Read H5 transform, calculate physical bounding box
         2. Resample both segmentations onto a unified mask-space grid
         3. Extract only the leg bounding box from the raw CT (bypasses OOM)
         4. Apply H5 transform to the cropped CT
         5. Center the patient at X=0
      -> combined_seg.nii + ct_cropped.nii (aligned, centered, right-side up)

### Converged pipeline

    combined_seg.nii (labels 1=femur_R, 2=femur_L,
                              3=tibia_R, 4=tibia_L,
                              5=fibula_R, 6=fibula_L,
                              7=talus_R, 8=talus_L)
      -> load_volume (SimpleITK)                    [fileio/volume.py]
      -> extract_masks -> BoneMask per bone          [imaging/masks.py]
      -> mask_to_mesh (marching cubes, world mm)     [imaging/mesh.py]
      -> mesh verification (watertight, volume)      [imaging/mesh.py]
      -> landmarks:
           femoral_head_centre (sphere fit)          [geometry/landmarks.py]
           knee_centre (two-condyle split)           [geometry/landmarks.py]
           ankle_centre (plafond + malleoli)         [geometry/landmarks.py]
      -> alignment angles (HKA, MAD, mLDFA, MPTA)    [geometry/alignment.py]
      -> hand-reference comparison                   [pipeline_demo.py]
      -> JSON summary per case                       [output/<case>/summary.json]
      -> report tables                               [make_report_tables.py]
      -> validation report                           [reports/validation.md]

### Second method (segmentation comparison)

    Combined segmentation + CT
      -> run_totalseg_all.py (OOM-safe wrapper)
           total task (femurs) + appendicular_bones task (tibia/fibula)
           each task: crop to bone bbox, run, wait for detach, paste back
      -> segmentation_full.nii.gz per task
      -> compare_segmentations.py (Dice, HD95 in mm)
      -> seg_results_<case>.json
      -> segmentation_errors.md

## Existing pipeline (no real data required)

The Docker container ships with a synthetic 8-bone volume generator so the
full pipeline can be exercised without downloading any CT data.

    demo_synthetic.py (creates 20x20x20 volume with 8 corners labelled)
      -> pipeline_demo.py (load, extract, mesh, JSON)
      -> /tmp/output/summary.json

    synthetic volume (CLI path)
      -> make_volume (zeros) -> describe -> CLI prints geometry
      -> write_info -> save_json -> info.json
      -> HTTP service: /health, /info (reads REPORT_FOLDER/info.json if present)

## Where each fact lives

- **How to run a stage**: `docs/runbook.md`
- **Why a design looks unusual**: `docs/decisions.md` (D001 to D043)
- **What the data is, licence, coverage**: `docs/data.md`
- **Subject-to-case mapping**: `docs/data.md` (must be updated whenever a new case is added)
- **Citations**: `CITATION.cff`
- **Rules for contributors and AI agents**: `AGENTS.md`
- **Call graphs at each stage**: `docs/FLOW.md`
- **Validation results**: `reports/validation.md`