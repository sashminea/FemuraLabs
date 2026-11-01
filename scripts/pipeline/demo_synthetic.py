#!/usr/bin/env python3
"""Generate a synthetic volume and run the pipeline demo on it."""
import os
import subprocess
from pathlib import Path

import numpy as np
import SimpleITK as sitk

def main():
    # 1. Create synthetic volume
    arr = np.zeros((20, 20, 20), dtype=np.uint8)
    arr[2:6, 2:6, 2:6] = 1      # femur_R
    arr[2:6, 14:18, 2:6] = 2    # femur_L
    arr[2:6, 2:6, 14:18] = 3    # tibia_R
    arr[2:6, 14:18, 14:18] = 4  # tibia_L
    arr[14:18, 2:6, 2:6] = 5    # fibula_R
    arr[14:18, 14:18, 2:6] = 6  # fibula_L
    arr[14:18, 2:6, 14:18] = 7  # talus_R
    arr[14:18, 14:18, 14:18] = 8# talus_L

    image = sitk.GetImageFromArray(arr)
    image.SetSpacing((10.0, 10.0, 10.0))
    image.SetOrigin((0.0, 0.0, 0.0))
    
    tmp_dir = Path("/tmp/synthetic_case")
    tmp_dir.mkdir(exist_ok=True)
    case_path = tmp_dir / "combined_seg.nii"
    sitk.WriteImage(image, str(case_path))

    print(f"Generated synthetic case at {case_path}")
    print("Running pipeline...")

    out_dir = Path("/tmp/output")
    out_dir.mkdir(exist_ok=True)

    env = {**os.environ, "PYTHONPATH": "/app/src"}
    subprocess.run([
        "python", "scripts/pipeline/pipeline_demo.py",
        "--case", str(case_path),
        "--out", str(out_dir)
    ], check=True, env=env)

if __name__ == "__main__":
    main()