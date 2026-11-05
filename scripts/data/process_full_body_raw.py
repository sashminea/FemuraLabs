#!/usr/bin/env python3
"""Apply H5 transform, combine segmentations, center, and crop without OOM."""
import argparse
import gc
import logging
from itertools import product
from pathlib import Path

import numpy as np
import SimpleITK as sitk

FALLBACK_MAP = {
    "thighs": {"Femur_R": 1, "Femur_L": 2},
    "shanks": {"Tibia_R": 1, "Fibula_R": 2, "Talus_R": 3, "Fibula_L": 8, "Tibia_L": 4, "Talus_L": 10}
}
TARGET_LABELS = {
    "Femur_R": 1, "Femur_L": 2, "Tibia_R": 3, "Tibia_L": 4,
    "Fibula_R": 5, "Fibula_L": 6, "Talus_R": 7, "Talus_L": 8
}

def setup_logging():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S')

def load_segment_map(seg_path: Path, is_thighs: bool) -> dict:
    img = sitk.ReadImage(str(seg_path))
    mapping = {}
    for key in img.GetMetaDataKeys():
        if key.endswith("_Name"):
            prefix = key.split("_")[0]
            name = img.GetMetaData(key)
            label_key = f"{prefix}_LabelValue"
            if label_key in img.GetMetaDataKeys():
                mapping[name] = int(img.GetMetaData(label_key))
    return mapping if mapping else (FALLBACK_MAP["thighs"] if is_thighs else FALLBACK_MAP["shanks"])

def main():
    setup_logging()
    p = argparse.ArgumentParser()
    p.add_argument("--ct", type=Path, required=True)
    p.add_argument("--thighs-seg", type=Path, required=True)
    p.add_argument("--shanks-seg", type=Path, required=True)
    p.add_argument("--transform", type=Path, required=False, default=None)
    p.add_argument("--out-dir", type=Path, required=True)
    p.add_argument("--margin-mm", type=float, default=20.0)
    args = p.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)

    try:
        tx = sitk.ReadTransform(str(args.transform)) if args.transform else sitk.Transform()

        # --- 1. Load Segmentations & Validate ---
        logging.info("Loading segmentations...")
        t_img = sitk.ReadImage(str(args.thighs_seg))
        s_img = sitk.ReadImage(str(args.shanks_seg))

        assert t_img.GetNumberOfComponentsPerPixel() == 1, "Thighs seg is multi-component!"
        assert s_img.GetNumberOfComponentsPerPixel() == 1, "Shanks seg is multi-component!"

        t_arr = sitk.GetArrayFromImage(t_img)
        s_arr = sitk.GetArrayFromImage(s_img)

        # --- 2. Physical bounding box of nonzero voxels (direction-safe) ---
        logging.info("Calculating physical bounding box of segmentations...")
        def bbox_corners(img, arr):
            idx = np.where(arr > 0)
            if len(idx[0]) == 0:
                return []
            lo = [int(idx[2].min()), int(idx[1].min()), int(idx[0].min())]  # x, y, z
            hi = [int(idx[2].max()), int(idx[1].max()), int(idx[0].max())]
            return [img.TransformIndexToPhysicalPoint(list(c)) for c in product(*zip(lo, hi))]

        pts = bbox_corners(t_img, t_arr) + bbox_corners(s_img, s_arr)
        if not pts:
            raise ValueError("Both segmentations are empty.")

        phys_min = [min(p[k] for p in pts) - args.margin_mm for k in range(3)]
        phys_max = [max(p[k] for p in pts) + args.margin_mm for k in range(3)]
        logging.info(f"Mask-space bbox: {[round(x,1) for x in phys_min]} -> {[round(x,1) for x in phys_max]}")

        # --- 3. Unified grid in mask space, identity direction ---
        spacing = t_img.GetSpacing()
        size = [int(np.ceil((phys_max[k] - phys_min[k]) / spacing[k])) + 1 for k in range(3)]

        ref_img = sitk.Image(size, sitk.sitkUInt8)
        ref_img.SetOrigin(phys_min)
        ref_img.SetSpacing(spacing)
        ref_img.SetDirection((1, 0, 0, 0, 1, 0, 0, 0, 1))

        logging.info("Merging labels on unified grid...")
        t_ref = sitk.Resample(t_img, ref_img, sitk.Transform(), sitk.sitkNearestNeighbor, 0)
        s_ref = sitk.Resample(s_img, ref_img, sitk.Transform(), sitk.sitkNearestNeighbor, 0)
        
        t_arr_ref = sitk.GetArrayFromImage(t_ref)
        s_arr_ref = sitk.GetArrayFromImage(s_ref)
        del t_ref, s_ref, t_img, s_img, t_arr, s_arr; gc.collect()

        combined_arr = np.zeros(t_arr_ref.shape, dtype=np.uint8)
        t_map = load_segment_map(args.thighs_seg, True)
        s_map = load_segment_map(args.shanks_seg, False)
        
        for name, target_id in TARGET_LABELS.items():
            if name in t_map:
                mask = (t_arr_ref == t_map[name])
                combined_arr[mask] = target_id
                logging.info(f"Mapped {name} from thighs (idx {t_map[name]}) -> {target_id} ({np.sum(mask)} voxels)")
            if name in s_map:
                mask = (s_arr_ref == s_map[name])
                combined_arr[mask] = target_id
                logging.info(f"Mapped {name} from shanks (idx {s_map[name]}) -> {target_id} ({np.sum(mask)} voxels)")

        del t_arr_ref, s_arr_ref; gc.collect()

        # Sanity check: ensure no mapped labels are empty
        present = set(np.unique(combined_arr)) - {0}
        missing = set(TARGET_LABELS.values()) - present
        if missing:
            logging.warning(f"Some labels missing after merge: {sorted(missing)} (this can happen if the source data didn't annotate them)")

        # --- 4. Crop Raw CT using Inverse Transform ---
        logging.info("Calculating raw CT crop box...")
        inv = tx.GetInverse()
        
        ct_reader = sitk.ImageFileReader()
        ct_reader.SetFileName(str(args.ct))
        ct_reader.ReadImageInformation()
        
        # Memory-safe geometry proxy
        geom = sitk.Image([1, 1, 1], sitk.sitkUInt8)
        geom.SetOrigin(ct_reader.GetOrigin())
        geom.SetSpacing(ct_reader.GetSpacing())
        geom.SetDirection(ct_reader.GetDirection())

        cont = []
        for c in product(*[(0, s - 1) for s in ref_img.GetSize()]):
            p_world = ref_img.TransformIndexToPhysicalPoint([int(v) for v in c])
            cont.append(geom.TransformPhysicalPointToContinuousIndex(inv.TransformPoint(p_world)))

        pad = 3
        lo = [max(0, int(np.floor(min(i[k] for i in cont))) - pad) for k in range(3)]
        hi = [min(ct_reader.GetSize()[k], int(np.ceil(max(i[k] for i in cont))) + pad + 1) for k in range(3)]
        if any(h <= l for l, h in zip(lo, hi)):
            raise ValueError(f"Crop box outside CT: lo={lo}, hi={hi}")

        logging.info(f"Extracting raw CT box: size={[h - l for l, h in zip(lo, hi)]}, index={lo}")
        ct_reader.SetExtractIndex(lo)
        ct_reader.SetExtractSize([h - l for l, h in zip(lo, hi)])
        ct_raw = ct_reader.Execute()
        del geom; gc.collect()

        # --- 5. Resample CT to Final Grid ---
        logging.info("Applying transform to cropped CT...")
        fill_val = -1000 if ct_raw.GetPixelID() in [sitk.sitkInt16, sitk.sitkInt32, sitk.sitkFloat32] else 0
        ct_final = sitk.Resample(ct_raw, ref_img, tx, sitk.sitkLinear, fill_val, ct_raw.GetPixelID())
        del ct_raw; gc.collect()

        seg_crop = sitk.GetImageFromArray(combined_arr)
        seg_crop.CopyInformation(ref_img)

        # --- 6. Center Patient at X=0 ---
        logging.info("Centering patient at X=0...")
        zi_R, yi_R, xi_R = np.where(combined_arr == 1)
        zi_L, yi_L, xi_L = np.where(combined_arr == 2)
        
        if len(xi_R) > 0 and len(xi_L) > 0:
            c_R = seg_crop.TransformContinuousIndexToPhysicalPoint((xi_R.mean(), yi_R.mean(), zi_R.mean()))
            c_L = seg_crop.TransformContinuousIndexToPhysicalPoint((xi_L.mean(), yi_L.mean(), zi_L.mean()))
            shift = -(c_R[0] + c_L[0]) / 2.0
            
            new_origin = (seg_crop.GetOrigin()[0] + shift, seg_crop.GetOrigin()[1], seg_crop.GetOrigin()[2])
            ct_final.SetOrigin(new_origin)
            seg_crop.SetOrigin(new_origin)
            logging.info(f"Shifted X by {shift:+.1f} mm to center patient.")

        # --- 7. Save ---
        ct_out = args.out_dir / "ct_cropped.nii"
        seg_out = args.out_dir / "combined_seg.nii"
        sitk.WriteImage(ct_final, str(ct_out))
        sitk.WriteImage(seg_crop, str(seg_out))
        logging.info("SUCCESS. Final size: " + str(ct_final.GetSize()))

    except Exception as e:
        logging.error(f"FATAL ERROR: {e}")
        raise

if __name__ == "__main__":
    raise SystemExit(main())