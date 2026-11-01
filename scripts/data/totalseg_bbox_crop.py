#!/usr/bin/env python3
"""Run TotalSegmentator on a tightly cropped CT, survive the OOM killer, and paste back."""
import argparse
import subprocess
import time
from pathlib import Path

import numpy as np
import SimpleITK as sitk

from femuralabs.toolkit.fileio.volume import load_volume
from femuralabs.toolkit.imaging.masks import extract_masks


def resample_image(image, new_spacing, interpolator=sitk.sitkLinear):
    original_size = image.GetSize()
    original_spacing = image.GetSpacing()
    new_size = [
        int(round(original_size[i] * original_spacing[i] / new_spacing[i]))
        for i in range(3)
    ]
    resampler = sitk.ResampleImageFilter()
    resampler.SetSize(new_size)
    resampler.SetOutputSpacing(new_spacing)
    resampler.SetOutputOrigin(image.GetOrigin())
    resampler.SetOutputDirection(image.GetDirection())
    resampler.SetInterpolator(interpolator)
    return resampler.Execute(image)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--ct", type=Path, required=True)
    p.add_argument("--ref", type=Path, required=True, help="Reference combined_seg.nii")
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--spacing", type=float, default=3.0)
    p.add_argument("--task", default="appendicular_bones")
    p.add_argument("--margin", type=int, default=20, help="Extra voxels around the bounding box")
    args = p.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)

    # 1. Resample CT to 3mm
    ct_img = sitk.ReadImage(str(args.ct))
    resampled_ct = resample_image(ct_img, (args.spacing,) * 3, sitk.sitkLinear)
    resampled_arr = sitk.GetArrayFromImage(resampled_ct)
    
    # 2. Find bounding box of all leg bones in the resampled grid
    ref_vol = load_volume(args.ref)
    ref_img = sitk.GetImageFromArray(ref_vol.array)
    ref_img.SetSpacing(ref_vol.spacing)
    ref_img.SetOrigin(ref_vol.origin)
    ref_img.SetDirection(ref_vol.direction)
    resampled_ref = resample_image(ref_img, (args.spacing,) * 3, sitk.sitkNearestNeighbor)
    ref_arr = sitk.GetArrayFromImage(resampled_ref)

    # We include all 6 main bones (excluding talus) to ensure the crop covers everything
    bone_mask = np.isin(ref_arr, [1, 2, 3, 4, 5, 6])
    if not np.any(bone_mask):
        raise ValueError("Reference mask has no bone voxels.")
    
    z_idx, y_idx, x_idx = np.where(bone_mask)
    z_min, z_max = int(z_idx.min()), int(z_idx.max()) + 1
    y_min, y_max = int(y_idx.min()), int(y_idx.max()) + 1
    x_min, x_max = int(x_idx.min()), int(x_idx.max()) + 1
    
    z_min = max(0, z_min - args.margin)
    z_max = min(resampled_arr.shape[0], z_max + args.margin)
    y_min = max(0, y_min - args.margin)
    y_max = min(resampled_arr.shape[1], y_max + args.margin)
    x_min = max(0, x_min - args.margin)
    x_max = min(resampled_arr.shape[2], x_max + args.margin)

    # 3. Crop the CT
    cropped_arr = resampled_arr[z_min:z_max, y_min:y_max, x_min:x_max]
    cropped_img = sitk.GetImageFromArray(cropped_arr)
    
    new_origin = (
        resampled_ct.GetOrigin()[0] + x_min * args.spacing,
        resampled_ct.GetOrigin()[1] + y_min * args.spacing,
        resampled_ct.GetOrigin()[2] + z_min * args.spacing,
    )
    cropped_img.SetSpacing(resampled_ct.GetSpacing())
    cropped_img.SetDirection(resampled_ct.GetDirection())
    cropped_img.SetOrigin(new_origin)
    
    cropped_path = args.out / "ct_cropped.nii.gz"
    sitk.WriteImage(cropped_img, str(cropped_path))

    # 4. Run TotalSegmentator
    seg_output_base = args.out / "totalseg_cropped"
    cmd = [
        "TotalSegmentator",
        "-i", str(cropped_path),
        "-o", str(seg_output_base),
        "-ta", args.task,
        "--ml",
        "-d", "cpu",
        "-nr", "1",
        "-ns", "1",
    ]
    if args.task == "total":
        cmd.append("--fast")
        
    print(f"Running TotalSegmentator {args.task}...")
    
    # check=False is critical because the OS will kill the parent process when RAM fills up.
    # However, the TotalSegmentator child process will detach and keep running.
    subprocess.run(cmd, check=False)

    # 5. Wait for the background zombie process to finish saving the file
    print("Parent process died (OOM). Waiting for background process to save output...")
    expected_nii = Path(str(seg_output_base) + ".nii")
    expected_nii_gz = Path(str(seg_output_base) + ".nii.gz")
    
    timeout = 600 # Wait up to 10 minutes
    start_time = time.time()
    
    while not expected_nii.exists() and not expected_nii_gz.exists():
        if time.time() - start_time > timeout:
            raise TimeoutError("TotalSegmentator took too long to save the file.")
        time.sleep(2)
        
    print("File saved! Pasting back to full grid...")
    
    # 6. Paste back and upsample
    seg_file = expected_nii if expected_nii.exists() else expected_nii_gz
    seg_img = sitk.ReadImage(str(seg_file))
    seg_arr = sitk.GetArrayFromImage(seg_img)
    
    full_resampled_arr = np.zeros(resampled_arr.shape, dtype=np.uint8)
    full_resampled_arr[z_min:z_max, y_min:y_max, x_min:x_max] = seg_arr
    
    full_resampled_img = sitk.GetImageFromArray(full_resampled_arr)
    full_resampled_img.CopyInformation(resampled_ct)

    resampler = sitk.ResampleImageFilter()
    resampler.SetReferenceImage(ct_img)
    resampler.SetInterpolator(sitk.sitkNearestNeighbor)
    full_mask = resampler.Execute(full_resampled_img)

    out_path = args.out / "segmentation_full.nii.gz"
    sitk.WriteImage(full_mask, str(out_path))
    print(f"Successfully wrote {out_path}")


if __name__ == "__main__":
    raise SystemExit(main())