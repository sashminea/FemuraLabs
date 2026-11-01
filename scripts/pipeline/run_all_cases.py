#!/usr/bin/env python3
"""Run pipeline_demo.py on all three cases and generate reports."""
import os
import subprocess
import sys
from pathlib import Path

CASES = ["case01", "case02", "case03"]

def main():
    Path("reports").mkdir(exist_ok=True)
    Path("output").mkdir(exist_ok=True)
    
    for case in CASES:
        print(f"\n========================================\nRunning {case}...\n========================================")
        cmd = [
            sys.executable, "scripts/pipeline/pipeline_demo.py", # <--- updated path
            "--case", f"data/raw/{case}/combined_seg.nii",
            "--out", f"output/{case}",
            "--compare", f"data/ref/landmarks_{case}.mrk.json",
            "--angles"
        ]
        env = {**os.environ, "PYTHONPATH": "src"}
        subprocess.run(cmd, check=True, env=env)
        print(f"Finished {case}")

if __name__ == "__main__":
    main()