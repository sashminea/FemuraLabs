#!/usr/bin/env python3
"""Generate markdown reports from the pipeline JSON outputs."""
import json
from pathlib import Path
import numpy as np

CASES = ["case01", "case02", "case03", "case04", "case05", "case06", "case07", "case08"]
OUT_DIR = Path("output")
REPORT_DIR = Path("reports")

def load_summary(case):
    path = OUT_DIR / case / "summary.json"
    if not path.exists():
        print(f"Warning: {path} not found. Run the pipeline first.")
        return None
    return json.loads(path.read_text())

def main():
    REPORT_DIR.mkdir(exist_ok=True)
    
    lm_rows = []
    angle_rows = []
    
    # We'll collect angle diffs to compute overall bias later
    angle_diffs = {}

    for case in CASES:
        d = load_summary(case)
        if not d: continue
        
        # --- Landmarks ---
        if "landmarks" in d:
            for name, data in d["landmarks"].items():
                lm_rows.append(
                    f"| {case} | {name:<18} | {data['auto'][0]:>7.1f}, {data['auto'][1]:>7.1f}, {data['auto'][2]:>7.1f} | "
                    f"{data['hand'][0]:>7.1f}, {data['hand'][1]:>7.1f}, {data['hand'][2]:>7.1f} | {data['error_mm']:>5.2f} |"
                )
                
        # --- Angles ---
        if "angles" in d:
            for name, data in d["angles"].items():
                diff = data["diff_deg"]
                angle_rows.append(
                    f"| {case} | {name:<9} | {data['auto']:>7.2f} | {data['hand']:>7.2f} | {diff:>+7.2f} |"
                )
                angle_diffs.setdefault(name, []).append(diff)

    # Write landmark_errors.md
    lm_md = [
        "# Landmark Errors",
        "",
        "Comparison of automatic landmark detection vs. hand-placed reference.",
        "",
        "| Case | Landmark | Auto (x, y, z) | Hand (x, y, z) | Error (mm) |",
        "|---|---|---|---|---|"
    ] + lm_rows
    (REPORT_DIR / "landmark_errors.md").write_text("\n".join(lm_md) + "\n")
    print(f"Wrote reports/landmark_errors.md")

    # Write angles_case.md
    angle_md = [
        "# Alignment Angles",
        "",
        "Comparison of automatic angle computation vs. hand-placed reference.",
        "",
        "| Case | Angle | Auto (deg) | Hand (deg) | Difference (deg) |",
        "|---|---|---|---|---|"
    ] + angle_rows + [
        "",
        "## Summary Statistics (Bias and Mean Absolute Difference)",
        "",
        "| Angle | n | Bias (mean diff) | Mean Abs Difference |",
        "|---|---|---|---|"
    ]
    
    for name, diffs in angle_diffs.items():
        arr = np.array(diffs)
        bias = np.mean(arr)
        mad = np.mean(np.abs(arr))
        angle_md.append(f"| {name:<9} | {len(arr):>2} | {bias:>+7.2f} | {mad:>7.2f} |")

    (REPORT_DIR / "angles_case.md").write_text("\n".join(angle_md) + "\n")
    print(f"Wrote reports/angles_case.md")

    # --- Segmentation Comparison ---
    seg_md = [
        "# Segmentation Metrics (TotalSegmentator vs Reference)",
        "",
        "| Case | Bone | Dice | HD95 (mm) |",
        "|---|---|---|---|"
    ]
    for case in CASES:
        path = Path(f"reports/seg_results_{case}.json")
        if not path.exists(): continue
        seg_data = json.loads(path.read_text())
        for bone, metrics in seg_data.items():
            seg_md.append(f"| {case} | {bone} | {metrics['dice']:.3f} | {metrics['hd95_mm']:.2f} |")
            
    (REPORT_DIR / "segmentation_errors.md").write_text("\n".join(seg_md) + "\n")
    print(f"Wrote reports/segmentation_errors.md")

if __name__ == "__main__":
    main()