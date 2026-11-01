#!/usr/bin/env python3
"""Run TotalSegmentator and compare, all in one script."""
import os
import subprocess
import sys
from pathlib import Path

env = {**os.environ, "PYTHONPATH": "src"}

def run_cmd(cmd):
    subprocess.run(cmd, check=True, env=env)

def main():
    cases = ["case02", "case03"]
    
    for case in cases:
        print(f"\n========================================\nProcessing {case}\n========================================")
        base_dir = Path(f"data/raw/{case}")
        ct_path = base_dir / f"{case}_ct.nii.gz"
        ref_path = base_dir / "combined_seg.nii"
        
        # 1. Femurs (Total Task)
        out_total = f"output/totalseg/{case}"
        run_cmd([
            sys.executable, "scripts/data/totalseg_bbox_crop.py",
            "--ct", str(ct_path), "--ref", str(ref_path),
            "--out", out_total, "--task", "total"
        ])
        
        # Rename femurs so appendicular doesn't overwrite it
        Path(f"{out_total}/segmentation_full.nii.gz").rename(f"{out_total}/segmentation_femurs.nii.gz")
        
        # 2. Tibia/Fibula (Appendicular Task)
        out_app = f"output/totalseg/{case}_appendicular"
        run_cmd([
            sys.executable, "scripts/data/totalseg_bbox_crop.py",
            "--ct", str(ct_path), "--ref", str(ref_path),
            "--out", out_app, "--task", "appendicular_bones"
        ])
        
        # 3. Compare
        print(f"--- {case}: Comparing ---")
        run_cmd([
            sys.executable, "scripts/pipeline/compare_segmentations.py",
            "--ref", str(ref_path),
            "--ts-total", f"{out_total}/segmentation_femurs.nii.gz",
            "--ts-app", f"{out_app}/segmentation_full.nii.gz",
            "--out", f"reports/seg_results_{case}.json"
        ])

if __name__ == "__main__":
    main()