#!/usr/bin/env python3
"""Merge two Slicer-exported NIfTIs (thighs, shanks) into a 6-label file.

Reads the .labels.csv that Slicer writes next to each export to look up
source label values *by name*, not by assuming case01's numbers.
Case01 thighs: Femur_R=5, Femur_L=6 (Threshold artefact at 1).
Case03 thighs: Femur_R=1, Femur_L=2 (no artefact).
Hardcoding either silently wrong on the other subject.

Destination labels (fixed by docs/data.md and D032):
  1 femur_R, 2 femur_L, 3 tibia_R, 4 tibia_L,
  5 fibula_R, 6 fibula_L, 7 talus_R, 8 talus_L
Talus added 2026-10-31 to give the hand-placer a visible talar dome
reference and to unblock a future talus-based ankle_centre rule
(D032's "why no talus yet" note).
"""
import argparse
import csv
import sys
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
    raise SystemExit(f"unexpected suffix on {nii_path}; expected .nii or .nii.gz")


def check_same_grid(a, b):
    """Raise if two SimpleITK images are not on identical grids."""
    if a.GetSize() != b.GetSize():
        raise SystemExit(
            f"size mismatch: {a.GetSize()} vs {b.GetSize()}. One export was "
            "not resampled onto the full-volume grid."
        )
    if not np.allclose(a.GetSpacing(), b.GetSpacing()):
        raise SystemExit(f"spacing mismatch: {a.GetSpacing()} vs {b.GetSpacing()}")
    if not np.allclose(a.GetOrigin(), b.GetOrigin()):
        raise SystemExit(f"origin mismatch: {a.GetOrigin()} vs {b.GetOrigin()}")
    if not np.allclose(a.GetDirection(), b.GetDirection()):
        raise SystemExit("direction mismatch")


def merge(thighs_nii, shanks_nii, out_path,
          thighs_csv=None, shanks_csv=None):
    thighs_csv = Path(thighs_csv) if thighs_csv else derive_csv(thighs_nii)
    shanks_csv = Path(shanks_csv) if shanks_csv else derive_csv(shanks_nii)

    thighs_img = sitk.ReadImage(str(thighs_nii))
    shanks_img = sitk.ReadImage(str(shanks_nii))
    check_same_grid(thighs_img, shanks_img)

    t = sitk.GetArrayFromImage(thighs_img)
    s = sitk.GetArrayFromImage(shanks_img)
    t_lab = read_labels_csv(thighs_csv)
    s_lab = read_labels_csv(shanks_csv)

    for name in THIGHS_BONES:
        if name not in t_lab:
            raise SystemExit(f"{thighs_csv}: missing {name}")
    for name in SHANKS_BONES:
        if name not in s_lab:
            raise SystemExit(f"{shanks_csv}: missing {name}")

    merged = np.zeros(t.shape, dtype=np.uint8)
    for name, dst in DEST.items():
        src = (t_lab if name in THIGHS_BONES else s_lab)[name]
        mask = (t if name in THIGHS_BONES else s) == src
        n = int(mask.sum())
        if n == 0:
            raise SystemExit(
                f"{name}: source label {src} has 0 voxels. "
                "The CSV and the array disagree, or the export is empty."
            )
        if np.any(merged[mask] != 0):
            raise SystemExit(
                f"{name}: would overwrite "
                f"{int(np.sum(merged[mask] != 0))} already-labelled voxels"
            )
        merged[mask] = dst
        print(f"  {name:<9} src {src:>2} -> dst {dst}  ({n:>8,} voxels)")

    out_img = sitk.GetImageFromArray(merged)
    out_img.CopyInformation(thighs_img)
    sitk.WriteImage(out_img, str(out_path))
    print(f"\nwrote {out_path}")
    print(f"  size   : {out_img.GetSize()}")
    print(f"  spacing: {out_img.GetSpacing()}")
    print(f"  labels : {np.unique(merged).tolist()}")


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--thighs", required=True, type=Path)
    p.add_argument("--shanks", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--thighs-csv", type=Path, default=None,
                   help="default: derived from --thighs")
    p.add_argument("--shanks-csv", type=Path, default=None,
                   help="default: derived from --shanks")
    args = p.parse_args(argv)
    merge(args.thighs, args.shanks, args.out,
          thighs_csv=args.thighs_csv, shanks_csv=args.shanks_csv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())