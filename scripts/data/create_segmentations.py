#!/usr/bin/env python3
"""Compare TotalSegmentator output against the reference combined_seg.nii."""
import argparse
import json
from pathlib import Path

import numpy as np

from femuralabs.toolkit.io_volume import load_volume
from femuralabs.toolkit.masks import extract_masks
from femuralabs.toolkit.metrics import dice_score, hd95

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--ref", type=Path, required=True, help="Reference combined_seg.nii")
    p.add_argument("--ts-total", type=Path, required=True, help="TotalSegmentator 'total' output (femurs)")
    p.add_argument("--ts-app", type=Path, required=True, help="TotalSegmentator 'appendicular' output (tibias/fibulas)")
    p.add_argument("--out", type=Path, required=True, help="Output JSON file for metrics")
    args = p.parse_args()

    print("Loading reference...")
    ref_vol = load_volume(args.ref)
    ref_masks = extract_masks(ref_vol)

    print("Loading TotalSegmentator outputs...")
    ts_total_vol = load_volume(args.ts_total)
    ts_app_vol = load_volume(args.ts_app)

    # We need to map TotalSegmentator's integer labels to bone names.
    # TotalSegmentator usually outputs a class map file, but to be safe,
    # we will identify them by looking at the centroids.
    # We know that femur is the highest Z, tibia is lower, fibula is lateral.
    
    ts_masks = {}
    
    # Helper to extract masks from a TS volume by anatomical rules
    def extract_ts_masks(vol, is_thighs):
        D = np.array(vol.direction).reshape(3,3)
        S = np.array(vol.spacing)
        O = np.array(vol.origin)
        
        labels = [l for l in np.unique(vol.array) if l != 0]
        for l in labels:
            mask = vol.array == l
            if not np.any(mask): continue
            
            zi, yi, xi = np.where(mask)
            xyz = np.stack([xi, yi, zi], axis=1)
            centroid = (O + (xyz * S) @ D.T).mean(axis=0)
            
            # Determine side: in LPS, Right is negative X
            side = "R" if centroid[0] < 0 else "L"
            
            if is_thighs:
                # The `total` task gives us femurs
                ts_masks[f"femur_{side}"] = mask
                print(f"  Mapped TS label {l} (thighs) -> femur_{side}")
            else:
                # The `appendicular_bones` task gives tibia and fibula.
                # Tibia is much larger in volume than fibula.
                if mask.sum() > 10000: # Heuristic: tibia is large, fibula is small
                    ts_masks[f"tibia_{side}"] = mask
                    print(f"  Mapped TS label {l} (shanks) -> tibia_{side}")
                else:
                    ts_masks[f"fibula_{side}"] = mask
                    print(f"  Mapped TS label {l} (shanks) -> fibula_{side}")

    extract_ts_masks(ts_total_vol, is_thighs=True)
    extract_ts_masks(ts_app_vol, is_thighs=False)

    # Now compute metrics
    results = {}
    print(f"\n{'Bone':<10} | {'Dice':<6} | {'HD95 (mm)':<10}")
    print("-" * 32)
    
    for bone in ["femur_R", "femur_L", "tibia_R", "tibia_L", "fibula_R", "fibula_L"]:
        if bone not in ref_masks or bone not in ts_masks:
            print(f"{bone:<10} | MISSING")
            continue
            
        ref_mask = ref_masks[bone].mask
        ts_mask = ts_masks[bone]
        
        # Ensure masks are boolean
        ref_mask = ref_mask.astype(bool)
        ts_mask = ts_mask.astype(bool)
        
        d = dice_score(ref_mask, ts_mask)
        h = hd95(ref_mask, ts_mask, spacing=ref_vol.spacing)
        
        print(f"{bone:<10} | {d:.3f}  | {h:>8.2f}")
        results[bone] = {"dice": round(d, 3), "hd95_mm": round(h, 2)}

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(results, indent=2))
    print(f"\nWrote {args.out}")

if __name__ == "__main__":
    raise SystemExit(main())