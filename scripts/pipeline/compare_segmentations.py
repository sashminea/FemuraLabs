#!/usr/bin/env python3
"""Compare TotalSegmentator output against the reference combined_seg.nii."""
import argparse
import gc
import json
from pathlib import Path

import numpy as np

from femuralabs.toolkit.fileio.volume import load_volume
from femuralabs.toolkit.geometry.metrics import dice_score, hd95
from femuralabs.toolkit.imaging.masks import LABEL_NAMES, fill_bone_interior


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--ref", type=Path, required=True)
    p.add_argument("--ts-total", type=Path, required=True)
    p.add_argument("--ts-app", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()

    print("Loading volumes...")
    ref_vol = load_volume(args.ref)
    ts_total_vol = load_volume(args.ts_total)
    ts_app_vol = load_volume(args.ts_app)

    ts_masks = {}
    # 1. Map Femurs from ts_total
    ts_masks["femur_L"] = ts_total_vol.array == 75
    ts_masks["femur_R"] = ts_total_vol.array == 76

    # 2. Map Tibias and Fibulas from ts_app
    O = np.array(ts_app_vol.origin)
    S = np.array(ts_app_vol.spacing)
    D = np.array(ts_app_vol.direction).reshape(3, 3)
    x_mid = int(round((0 - O[0]) / (D[0, 0] * S[0])))
    print(f"Midline is at array index x={x_mid}")

    tib_raw = ts_app_vol.array == 2
    ts_masks["tibia_R"] = tib_raw.copy(); ts_masks["tibia_R"][:, :, x_mid:] = False
    ts_masks["tibia_L"] = tib_raw.copy(); ts_masks["tibia_L"][:, :, :x_mid] = False

    fib_raw = ts_app_vol.array == 3
    ts_masks["fibula_R"] = fib_raw.copy(); ts_masks["fibula_R"][:, :, x_mid:] = False
    ts_masks["fibula_L"] = fib_raw.copy(); ts_masks["fibula_L"][:, :, :x_mid] = False

    results = {}
    print(f"\n{'Bone':<10} | {'Dice':<6} | {'Raw Dice':<8} | {'HD95 (mm)':<10}")
    print("-" * 42)

    for ref_label, bone in LABEL_NAMES.items():
        if ref_label > 6: continue # Skip talus
        if bone not in ts_masks: continue

        ref_raw = ref_vol.array == ref_label
        ref_mask = fill_bone_interior(ref_raw)
        ts_mask = ts_masks[bone]

        d_raw = dice_score(ref_raw, ts_mask)
        d = dice_score(ref_mask, ts_mask)
        h = hd95(ref_mask, ts_mask, spacing=ref_vol.spacing)

        print(f"{bone:<10} | {d:.3f}  | {d_raw:.3f}    | {h:>8.2f}")
        results[bone] = {"dice": round(d, 3), "dice_unfilled": round(d_raw, 3), "hd95_mm": round(h, 2)}

        del ref_raw, ref_mask, ts_mask
        gc.collect()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(results, indent=2))
    print(f"\nWrote {args.out}")

if __name__ == "__main__":
    raise SystemExit(main())