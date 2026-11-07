#!/usr/bin/env python3
"""Run sliding-window inference on a raw CT and save as combined_seg.nii."""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import SimpleITK as sitk
import torch

from common import build_model, predict_volume
from validate import split_sides


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--checkpoint", type=Path, required=True)
    p.add_argument("--ct", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--merge-sides", action=argparse.BooleanOptionalAction, default=True)
    p.add_argument("--spacing", type=float, default=1.5)
    args = p.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    n_classes = 5 if args.merge_sides else 9
    model = build_model(16, n_classes).to(device)
    
    print(f"Loading checkpoint: {args.checkpoint}")
    ck = torch.load(args.checkpoint, map_location=device, weights_only=True)
    model.load_state_dict(ck["model"])
    model.eval()

    print(f"Loading CT: {args.ct}")
    ct_img = sitk.ReadImage(str(args.ct))
    
    # Resample native to 1.5mm
    old_sp = np.array(ct_img.GetSpacing())
    old_size = np.array(ct_img.GetSize())
    new_sp = np.full(3, args.spacing)
    new_size = np.ceil(old_size * old_sp / new_sp - 1e-6).astype(int)
    direction = np.array(ct_img.GetDirection()).reshape(3, 3)
    new_origin = np.array(ct_img.GetOrigin()) + direction @ (0.5 * (new_sp - old_sp))
    
    ref = sitk.Image(list(new_size), sitk.sitkFloat32)
    ref.SetSpacing(tuple(new_sp))
    ref.SetOrigin(tuple(new_origin))
    ref.SetDirection(ct_img.GetDirection())
    
    print(f"Resampling to {args.spacing}mm...")
    ct_rs = sitk.Resample(ct_img, ref, sitk.Transform(), sitk.sitkLinear, -1024, sitk.sitkInt16)
    ct_arr = sitk.GetArrayFromImage(ct_rs)
    
    print("Running sliding-window inference...")
    pred_rs = predict_volume(model, ct_arr, 96, 2, 0.5, device)
    
    if args.merge_sides:
        print("Splitting left/right...")
        meta = {"resampled": {"origin": ref.GetOrigin(), "spacing": ref.GetSpacing()}}
        pred_rs = split_sides(pred_rs, meta)
        
    print("Upsampling to native grid...")
    pred_img = sitk.GetImageFromArray(pred_rs)
    pred_img.CopyInformation(ref)
    pred_native = sitk.Resample(pred_img, ct_img, sitk.Transform(), sitk.sitkNearestNeighbor, 0, sitk.sitkUInt8)
    
    sitk.WriteImage(pred_native, str(args.out))
    print(f"Successfully wrote {args.out}")


if __name__ == "__main__":
    main()