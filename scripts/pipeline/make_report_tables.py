#!/usr/bin/env python3
"""Generate markdown reports from the pipeline JSON outputs."""
import json
from pathlib import Path
import numpy as np

CASES = [f"case{i:02d}" for i in range(1, 9)]
OUT_DIR = Path("output")
REPORT_DIR = Path("reports")

def load_summary(case):
    path = OUT_DIR / case / "summary.json"
    if not path.exists():
        return None
    return json.loads(path.read_text())

def main():
    REPORT_DIR.mkdir(exist_ok=True)
    
    lm_rows = []
    angle_rows = []
    angle_diffs = {}

    for case in CASES:
        d = load_summary(case)
        if not d: continue
        
        if "landmarks" in d:
            for name, data in d["landmarks"].items():
                delta = data.get("delta_mm", [0, 0, 0])
                lm_rows.append(
                    f"| {case} | {name:<18} | {data['error_mm']:>5.2f} | "
                    f"({delta[0]:+.1f}, {delta[1]:+.1f}, {delta[2]:+.1f}) |"
                )
                
        if "angles" in d:
            for name, data in d["angles"].items():
                diff = data["diff_deg"]
                angle_rows.append(f"| {case} | {name:<9} | {data['auto']:>7.2f} | {data['hand']:>7.2f} | {diff:>+7.2f} |")
                angle_diffs.setdefault(name, []).append(diff)

    # Write landmark_errors.md
    lm_md = [
        "# Landmark Errors",
        "",
        "| Case | Landmark | Error (mm) | Delta (x, y, z mm) |",
        "|---|---|---|---|"
    ] + lm_rows
    (REPORT_DIR / "landmark_errors.md").write_text("\n".join(lm_md) + "\n")
    print("Wrote reports/landmark_errors.md")

    # Write angles_case.md
    angle_md = [
        "# Alignment Angles",
        "",
        "| Case | Angle | Auto (deg) | Hand (deg) | Difference (deg) |",
        "|---|---|---|---|---|"
    ] + angle_rows + [
        "",
        "## Summary Statistics",
        "",
        "| Angle | n | Bias | SD | Median abs | Mean abs |",
        "|---|---|---|---|---|---|"
    ]
    
    for name, diffs in angle_diffs.items():
        arr = np.array(diffs)
        bias = np.mean(arr)
        mad = np.mean(np.abs(arr))
        sd = np.std(arr, ddof=1) if len(arr) > 1 else 0
        med_abs = np.median(np.abs(arr))
        angle_md.append(f"| {name:<9} | {len(arr):>2} | {bias:>+7.2f} | {sd:>6.2f} | {med_abs:>6.2f} | {mad:>7.2f} |")

    (REPORT_DIR / "angles_case.md").write_text("\n".join(angle_md) + "\n")
    print("Wrote reports/angles_case.md")

    # Write segmentation_errors.md
    seg_md = [
        "# Segmentation Metrics",
        "",
        "| Case | Bone | Dice (filled) | Dice (raw) | HD95 (mm) |",
        "|---|---|---|---|---|"
    ]
    for case in CASES:
        path = REPORT_DIR / f"seg_results_{case}.json"
        if not path.exists(): continue
        seg_data = json.loads(path.read_text())
        for bone, metrics in seg_data.items():
            d_filled = metrics.get('dice', 0.0)
            d_raw = metrics.get('dice_unfilled', 0.0)
            hd = metrics.get('hd95_mm', 0.0)
            seg_md.append(f"| {case} | {bone} | {d_filled:.3f} | {d_raw:.3f} | {hd:.2f} |")
            
    (REPORT_DIR / "segmentation_errors.md").write_text("\n".join(seg_md) + "\n")
    print("Wrote reports/segmentation_errors.md")

if __name__ == "__main__":
    main()