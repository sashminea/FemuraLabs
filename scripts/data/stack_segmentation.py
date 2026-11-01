#!/usr/bin/env python3
"""Stack two Slicer-exported NIfTIs (thighs, shanks) into a 8-label file.

Use this when the source data ships as two separate half-volumes (e.g.,
case02's 266 and 269 folders) rather than one full-limb volume with two
segmentations drawn on it. This script physically concatenates the two
arrays along the Z-axis and applies the same DEST label mapping used by
merge_segmentation.py.
"""
import argparse
import csv
from pathlib import Path

import numpy as np
import SimpleITK as sitk

DEST = {"Femur_R": 1, "Femur_L": 2, "Tibia_R": 3, "Tibia_L": 4,
        "Fibula_R": 5, "Fibula_L": 6, "Talus_R": 7, "Talus_L": 8}
THIGHS_BONES = {"Femur_R", "Femur_L"}
SHANKS_BONES = {"Tibia_R", "Tibia_L", "Fibula_R", "Fibula_L",
                "Talus_R", "Talus_L"}

def read_labels_csv(path):
    with open(path, newline="") as f:
        return {row["Name"]: int(row["LabelValue"]) for row in csv.DictReader(f)}

def derive_csv(nii_path):
    p = str(nii_path)
    for suf in (".nii.gz", ".nii"):
        if p.endswith(suf):
            return Path(p[:-len(suf)] + ".labels.csv")
    raise SystemExit(f"unexpected suffix on {nii_path}")

def stack(thighs_nii, shanks_nii, out_path,
          thighs_csv=None, shanks_csv=None):
    thighs_csv = Path(thighs_csv) if thighs_csv else derive_csv(thighs_nii)
    shanks_csv = Path(shanks_csv) if shanks_csv else derive_csv(shanks_nii)

    thighs_img = sitk.ReadImage(str(thighs_nii))
    shanks_img = sitk.ReadImage(str(shanks_nii))

    if thighs_img.GetSize()[:2] != shanks_img.GetSize()[:2]:
        raise SystemExit(f"X/Y size mismatch: {thighs_img.GetSize()} vs {shanks_img.GetSize()}")
    if not np.allclose(thighs_img.GetSpacing(), shanks_img.GetSpacing()):
        raise SystemExit(f"spacing mismatch: {thighs_img.GetSpacing()} vs {shanks_img.GetSpacing()}")
    if not np.allclose(thighs_img.GetDirection(), shanks_img.GetDirection()):
        raise SystemExit("direction mismatch")
    if not np.allclose(thighs_img.GetOrigin()[:2], shanks_img.GetOrigin()[:2]):
        raise SystemExit(f"X/Y origin mismatch: {thighs_img.GetOrigin()[:2]} vs {shanks_img.GetOrigin()[:2]}")

    # Decide which array is on top by comparing Z-origins
    if thighs_img.GetOrigin()[2] > shanks_img.GetOrigin()[2]:
        top_img, top_csv, top_bones = thighs_img, thighs_csv, THIGHS_BONES
        bottom_img, bottom_csv, bottom_bones = shanks_img, shanks_csv, SHANKS_BONES
        print("stacking: shanks on bottom, thighs on top")
    else:
        top_img, top_csv, top_bones = shanks_img, shanks_csv, SHANKS_BONES
        bottom_img, bottom_csv, bottom_bones = thighs_img, thighs_csv, THIGHS_BONES
        print("stacking: thighs on bottom, shanks on top")

    t_arr = sitk.GetArrayFromImage(top_img)
    b_arr = sitk.GetArrayFromImage(bottom_img)
    
    t_lab = read_labels_csv(top_csv)
    b_lab = read_labels_csv(bottom_csv)

    for name in top_bones:
        if name not in t_lab:
            raise SystemExit(f"{top_csv}: missing {name}")
    for name in bottom_bones:
        if name not in b_lab:
            raise SystemExit(f"{bottom_csv}: missing {name}")

    # Create empty combined array
    merged = np.zeros((t_arr.shape[0] + b_arr.shape[0], t_arr.shape[1], t_arr.shape[2]), dtype=np.uint8)

    # Place top-half labels
    for name in top_bones:
        src = t_lab[name]
        mask = (t_arr == src)
        merged[b_arr.shape[0]:, :, :][mask] = DEST[name]
        
    # Place bottom-half labels
    for name in bottom_bones:
        src = b_lab[name]
        mask = (b_arr == src)
        merged[:b_arr.shape[0], :, :][mask] = DEST[name]

    out_img = sitk.GetImageFromArray(merged)
    out_img.SetSpacing(top_img.GetSpacing())
    out_img.SetDirection(top_img.GetDirection())
    out_img.SetOrigin(bottom_img.GetOrigin())
    sitk.WriteImage(out_img, str(out_path))

    print(f"\nwrote {out_path}")
    print(f"  size   : {out_img.GetSize()}")
    print(f"  spacing: {out_img.GetSpacing()}")
    print(f"  origin : {out_img.GetOrigin()}")
    print(f"  labels : {np.unique(merged).tolist()}")
    
    for name, dst in DEST.items():
        n = int((merged == dst).sum())
        print(f"  {name:<9} -> {dst}  ({n:>8,} voxels)")

def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--thighs", required=True, type=Path)
    p.add_argument("--shanks", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--thighs-csv", type=Path, default=None)
    p.add_argument("--shanks-csv", type=Path, default=None)
    args = p.parse_args(argv)
    stack(args.thighs, args.shanks, args.out, thighs_csv=args.thighs_csv, shanks_csv=args.shanks_csv)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())