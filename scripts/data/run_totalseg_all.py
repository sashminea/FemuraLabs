#!/usr/bin/env python3
"""Run TotalSegmentator, paste back, and compare, all in one script."""
import os
import subprocess
import sys
import time
from pathlib import Path

# Ensure our local toolkit is importable
env = {**os.environ, "PYTHONPATH": "src"}

def run_cmd(cmd):
    # check=False is critical: TotalSegmentator gets OOM killed at the very end,
    # but it writes the output file first. We want to catch the crash and continue.
    subprocess.run(cmd, check=False, env=env)

def process_task(case, task, out_dir, ref_path, ct_path):
    print(f"--- {case}: {task} ---")
    out_dir = Path(out_dir)
    
    run_cmd([
        sys.executable, "scripts/data/totalseg_bbox_crop.py",
        "--ct", str(ct_path), "--ref", str(ref_path),
        "--out", str(out_dir), "--task", task
    ])
    
    # Give the OS a second to flush the file to disk after the crash
    time.sleep(2)
    
    cropped_file = out_dir / "totalseg_cropped.nii"
    if cropped_file.exists():
        run_cmd([
            sys.executable, "scripts/data/paste_back.py",
            "--seg", str(cropped_file), "--ref-ct", str(ct_path),
            "--out", str(out_dir / "segmentation_full.nii.gz")
        ])
        return True
    else:
        print(f"ERROR: Failed to produce {task} for {case}")
        return False

def main():
    cases = ["case02", "case03"]
    
    for case in cases:
        print(f"\n========================================\nProcessing {case}\n========================================")
        base_dir = Path(f"data/raw/{case}")
        ct_path = base_dir / f"{case}_ct.nii.gz"
        ref_path = base_dir / "combined_seg.nii"
        
        # 1. Convert NRRD to NIfTI if missing
        if not ct_path.exists():
            print(f"Finding raw NRRD for {case} and converting to NIfTI...")
            nrrds = [p for p in base_dir.rglob('*.nrrd') if not p.name.endswith('.seg.nrrd')]
            nrrds.sort(key=lambda p: p.stat().st_size, reverse=True)
            if not nrrds:
                print(f"ERROR: No NRRD found for {case}. Skipping.")
                continue
            
            run_cmd([
                sys.executable, "-c", 
                f"from femuralabs.toolkit.io_volume import load_volume, save_nifti; "
                f"v = load_volume('{nrrds[0]}'); save_nifti(v, '{ct_path}')"
            ])
            
        # 2. Femurs (Total Task)
        out_total = f"output/totalseg/{case}"
        if process_task(case, "total", out_total, ref_path, ct_path):
        # Rename femurs so appendicular doesn't overwrite it
        src = Path(f"{out_total}/segmentation_full.nii.gz")
        dst = Path(f"{out_total}/segmentation_femurs.nii.gz")
        if src.exists():
            src.replace(dst)
        else:
            print(f"WARNING: {src} not found!")

        # 3. Tibia/Fibula (Appendicular Task)
        out_app = f"output/totalseg/{case}_appendicular"
        process_task(case, "appendicular_bones", out_app, ref_path, ct_path)
        
        # 4. Compare
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