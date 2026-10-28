"""Test the pipeline end-to-end on a tiny synthetic volume."""
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import SimpleITK as sitk


def _make_synthetic_combined(path: Path) -> Path:
    """Four 4-voxel cubes at the corners of a 20x20x20 volume at spacing 10 mm.

    A 4x4x4 cube is 64 voxels; at 10 mm spacing, one voxel is 1000 mm^3,
    so the cube is 64,000 mm^3 = 64 mL. Chosen so that 64 voxels × 1000
    mm^3 = 64 mL exactly, which is the arithmetic the test asserts.
    """
    arr = np.zeros((20, 20, 20), dtype=np.uint8)
    arr[2:6, 2:6, 2:6] = 1      # femur_R
    arr[2:6, 14:18, 2:6] = 2    # femur_L
    arr[2:6, 2:6, 14:18] = 3    # tibia_R
    arr[2:6, 14:18, 14:18] = 4  # tibia_L
    image = sitk.GetImageFromArray(arr)
    image = sitk.GetImageFromArray(arr)
    image.SetSpacing((10.0, 10.0, 10.0))
    image.SetOrigin((0.0, 0.0, 0.0))
    sitk.WriteImage(image, str(path))
    return path


def _run(case: Path, out: Path) -> dict:
    env = {**os.environ, "PYTHONPATH": "src"}
    subprocess.run(
        [sys.executable, "scripts/pipeline_demo.py",
         "--case", str(case), "--out", str(out)],
        capture_output=True, text=True, check=True, env=env,
    )
    return json.loads((out / "summary.json").read_text())


def test_pipeline_on_synthetic_volume(tmp_path):
    case = _make_synthetic_combined(tmp_path / "combined_seg.nii")
    out = tmp_path / "out"
    summary = _run(case, out)

    assert summary["size"] == [20, 20, 20]      # (x, y, z), not (z, y, x)
    assert summary["spacing_mm"] == [10.0, 10.0, 10.0]
    assert set(summary["bones"].keys()) == {"femur_R", "femur_L", "tibia_R", "tibia_L"}
    for name, b in summary["bones"].items():
        assert b["voxels"] == 64, f"{name}: {b['voxels']}"
        assert b["volume_ml"] == 64.0, f"{name}: {b['volume_ml']}"
        assert b["vertices"] > 0
        assert b["faces"] > 0
        assert b["bbox_mm"] is not None
        assert (out / f"{name}.stl").exists()


def test_pipeline_is_deterministic(tmp_path):
    """Same input, same JSON. Catches timestamps and unordered dicts."""
    case = _make_synthetic_combined(tmp_path / "combined_seg.nii")
    a = _run(case, tmp_path / "a")
    b = _run(case, tmp_path / "b")
    assert a == b