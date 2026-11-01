#!/usr/bin/env python3
"""Calculate agreement statistics for angles across all cases."""
import json
from pathlib import Path
from femuralabs.toolkit.geometry.stats import confidence_interval, bland_altman

CASES = ["case01", "case02", "case03"]

def main():
    # Collect all differences per angle type
    angle_diffs = {
        "HKA_R": [], "HKA_L": [],
        "mLDFA_R": [], "mLDFA_L": [],
        "MPTA_R": [], "MPTA_L": []
    }
    
    for case in CASES:
        path = Path(f"output/{case}/summary.json")
        if not path.exists():
            continue
        d = json.loads(path.read_text())
        angles = d.get("angles", {})
        
        for angle_name, data in angles.items():
            if angle_name in angle_diffs:
                angle_diffs[angle_name].append(data["diff_deg"])

    print(f"{'Angle':<8} | {'n':<2} | {'Bias (deg)':<10} | {'95% CI':<16} | {'Limits of Agreement':<20}")
    print("-" * 65)
    
    for name, diffs in angle_diffs.items():
        if len(diffs) < 2:
            continue
            
        # Confidence interval for the mean difference (bias)
        ci_lo, ci_hi = confidence_interval(diffs, confidence=0.95)
        
        # Bland-Altman limits of agreement
        bias, loa_lo, loa_hi = bland_altman(diffs)
        
        print(f"{name:<8} | {len(diffs):<2} | {bias:>+9.2f} | [{ci_lo:>+6.2f}, {ci_hi:>+6.2f}] | [{loa_lo:>+6.2f}, {loa_hi:>+6.2f}]")

if __name__ == "__main__":
    main()