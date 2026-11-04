#!/usr/bin/env python3
"""Fix geometry for split-volume subjects with the Upside-Down transform."""
import argparse
from pathlib import Path

import numpy as np
import SimpleITK as sitk

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--in", dest="in_path", type=Path, required=True, help="Raw combined_seg.nii")
    p.add_argument("--out", dest="out_path", type=Path, required=True, help="Fixed output path")
    args = p.parse_args()

    print(f"Loading {args.in_path}")
    img = sitk.ReadImage(str(args.in_path))
    arr = sitk.GetArrayFromImage(img)
    spacing = img.GetSpacing()

    # 1. Flip X and Z axes (Upside-down transform)
    arr_flipped = arr[:, :, ::-1]
    arr_flipped = arr_flipped[::-1, :, :]

    # 2. Find the array midpoint between the two femurs (labels 1 and 2)
    # to center the patient at X=0
    zi_R, yi_R, xi_R = np.where(arr_flipped == 1) # Right femur
    zi_L, yi_L, xi_L = np.where(arr_flipped == 2) # Left femur
    
    if len(xi_R) == 0 or len(xi_L) == 0:
        raise ValueError("Could not find both femurs (labels 1 and 2) to center the X axis.")
        
    x_mid_array = (xi_L.mean() + xi_R.mean()) / 2

    # 3. Calculate the new origin so that x_mid_array sits at world X=0
    new_origin_x = - (x_mid_array * spacing[0])

    out = sitk.GetImageFromArray(arr_flipped)
    out.SetSpacing(spacing)
    out.SetOrigin((new_origin_x, 0.0, 0.0))
    out.SetDirection((1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0))

    sitk.WriteImage(out, str(args.out_path))
    print(f"Calculated array midpoint: {x_mid_array:.1f}")
    print(f"Shifted X origin to: {new_origin_x:.1f} mm")
    print(f"Wrote fixed geometry to {args.out_path}")

if __name__ == "__main__":
    raise SystemExit(main())