#!/usr/bin/env python3
"""Run sliding-window inference on validation cases and compute metrics.

This script:
  1. Loads the model checkpoint.
  2. Runs sliding-window inference on the 1.5 mm resampled CTs.
  3. If --merge-sides is set, splits the 4 merged classes into left/right
     using connected components and the physical X coordinate.
  4. Upsamples the prediction back to the native grid.
  5. Computes Dice and HD95 against the filled native reference.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import SimpleITK as sitk
import torch
from scipy import ndimage as ndi

from common import (HU_MAX, HU_MIN, LABEL_NAMES_8, MERGED_NAMES,
                    apply_label_map, build_model, num_classes, predict_volume)
from femuralabs.toolkit.imaging.masks import fill_bone_interior
from femuralabs.toolkit.geometry.metrics import dice_score, hd95


def split_sides(merged_seg: np.ndarray, meta: dict) -> np.ndarray:
    """Split 1=femur, 2=tibia, 3=fibula, 4=talus into 8 labels using X-position."""
    final_seg = np.zeros_like(merged_seg, dtype=np.uint8)
    
    # Find the array X index where physical X = 0
    ox, oy, oz = meta["resampled"]["origin"]
    sx, sy, sz = meta["resampled"]["spacing"]
    x_mid_idx = int(round((0 - ox) / sx))

    for c in [1, 2, 3, 4]:
        mask = merged_seg == c
        if not mask.any():
            continue
        
        lab, n = ndi.label(mask)
        for i in range(1, n + 1):
            comp = lab == i
            _, _, cx = ndi.center_of_mass(comp)
            
            # LPS: Right side is negative X (cx < x_mid_idx)
            if cx < x_mid_idx:
                final_seg[comp] = (c - 1) * 2 + 1  # R label
            else:
                final_seg[comp] = (c - 1) * 2 + 2  # L label
                
    return final_seg


def upsample_to_native(pred_resampled: np.ndarray, meta: dict, native_img: sitk.Image) -> np.ndarray:
    """Upsample the 1.5 mm prediction back to the native grid."""
    pred_img = sitk.GetImageFromArray(pred_resampled)
    pred_img.SetSpacing(meta["resampled"]["spacing"])
    pred_img.SetOrigin(meta["resampled"]["origin"])
    pred_img.SetDirection(meta["resampled"]["direction"])

    upsampled = sitk.Resample(
        pred_img, native_img, sitk.Transform(), sitk.sitkNearestNeighbor, 0, sitk.sitkUInt8
    )
    return sitk.GetArrayFromImage(upsampled)


def main():
    p = argparse.ArgumentParser(description="Validate a trained segmentation model.")
    p.add_argument("--checkpoint", type=Path, required=True)
    p.add_argument("--data-dir", type=Path, default=Path("data/ml_npy"))
    p.add_argument("--val-cases", default="case07,case08")
    p.add_argument("--out-dir", type=Path, default=Path("reports/data"))
    p.add_argument("--merge-sides", action=argparse.BooleanOptionalAction, default=True)
    p.add_argument("--init-filters", type=int, default=16)
    p.add_argument("--patch", type=int, default=96, help="Sliding window ROI size")
    p.add_argument("--sw-batch-size", type=int, default=2)
    p.add_argument("--overlap", type=float, default=0.5)
    args = p.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    n_classes = num_classes(args.merge_sides)
    model = build_model(args.init_filters, n_classes).to(device)
    
    print(f"Loading checkpoint: {args.checkpoint}")
    ck = torch.load(args.checkpoint, map_location=device, weights_only=True)
    model.load_state_dict(ck["model"])
    model.eval()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    cases = [c for c in args.val_cases.split(",") if c]
    results = {}

    for case in cases:
        print(f"\n=== {case} ===")
        meta = json.loads((args.data_dir / f"{case}_meta.json").read_text())
        ct_rs = np.load(args.data_dir / f"{case}_ct.npy")
        
        # 1. Sliding window inference
        print("  Running sliding window inference...")
        pred_rs = predict_volume(model, ct_rs, args.patch, args.sw_batch_size, args.overlap, device)
        
        # 2. Split merged sides if necessary
        if args.merge_sides:
            print("  Splitting left/right via connected components...")
            pred_rs = split_sides(pred_rs, meta)
            
        # 3. Upsample to native grid
        print("  Upsampling to native grid...")
        native_img = sitk.ReadImage(f"data/raw/{case}/combined_seg.nii")
        native_arr = sitk.GetArrayFromImage(native_img)
        pred_native = upsample_to_native(pred_rs, meta, native_img)

        # 4. Compute metrics against filled native reference
        print(f"  Computing metrics (native spacing: {native_img.GetSpacing()})...")
        case_results = {}
        
        for label in range(1, 7):  # Skip talus (labels 7,8) to match compare_segmentations.py
            bone = LABEL_NAMES_8[label]
            ref_mask = fill_bone_interior(native_arr == label)
            pred_mask = pred_native == label
            
            if not ref_mask.any() and not pred_mask.any():
                continue
                
            d = dice_score(ref_mask, pred_mask)
            h = hd95(ref_mask, pred_mask, spacing=native_img.GetSpacing())
            
            print(f"  {bone:<10} | Dice: {d:.3f} | HD95: {h:>5.2f} mm")
            case_results[bone] = {"dice": round(d, 3), "hd95_mm": round(h, 2)}

        results[case] = case_results
        
        out_path = args.out_dir / f"seg_results_{case}.json"
        out_path.write_text(json.dumps(case_results, indent=2))
        print(f"  Saved {out_path}")

if __name__ == "__main__":
    main()