#!/usr/bin/env python3
"""Apply H5 transform, combine segmentations, center, and crop without OOM."""
import argparse
import gc
import logging
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
                label_val = int(img.GetMetaData(label_key))
                mapping[name] = label_val
            
    if mapping:
        logging.info(f"Dynamically loaded {len(mapping)} labels from {seg_path.name} header")
        return mapping
    logging.warning(f"No labels found in header for {seg_path.name}. Using fallback.")
    return FALLBACK_MAP["thighs"] if is_thighs else FALLBACK_MAP["shanks"]

def main():
    setup_logging()
    p = argparse.ArgumentParser()
    p.add_argument("--ct", type=Path, required=True)
    p.add_argument("--thighs-seg", type=Path, required=True)
    p.add_argument("--shanks-seg", type=Path, required=True)
    p.add_argument("--transform", type=Path, required=False, default=None, help="Optional H5 transform file")
    p.add_argument("--out-dir", type=Path, required=True)
    p.add_argument("--margin-mm", type=float, default=20.0)
    args = p.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)

    try:
        # --- 1. Load Transform ---
        if args.transform:
            logging.info(f"Loading H5 transform from {args.transform.name}...")
            tx = sitk.ReadTransform(str(args.transform))
        else:
            logging.info("No transform provided. Using identity transform.")
            tx = sitk.Transform()

        # --- 2. Load Segmentations & Combine Arrays ---
        logging.info("Loading segmentations...")
        t_img = sitk.ReadImage(str(args.thighs_seg))
        s_img = sitk.ReadImage(str(args.shanks_seg))
        
        logging.info("Aligning segmentations to a common grid...")
        s_aligned = sitk.Resample(s_img, t_img, sitk.Transform(), sitk.sitkNearestNeighbor, 0, sitk.sitkUInt8)
        del s_img; gc.collect()

        t_arr = sitk.GetArrayFromImage(t_img)
        s_arr = sitk.GetArrayFromImage(s_aligned)
        del t_img, s_aligned; gc.collect()

        logging.info("Combining labels dynamically...")
        combined_arr = np.zeros(t_arr.shape, dtype=np.uint8)
        t_map = load_segment_map(args.thighs_seg, is_thighs=True)
        s_map = load_segment_map(args.shanks_seg, is_thighs=False)
        
        for name, target_id in TARGET_LABELS.items():
            if name in t_map:
                mask = (t_arr == t_map[name])
                combined_arr[mask] = target_id
                logging.info(f"Mapped {name} from thighs (idx {t_map[name]}) -> {target_id} ({np.sum(mask)} voxels)")
            if name in s_map:
                mask = (s_arr == s_map[name])
                combined_arr[mask] = target_id
                logging.info(f"Mapped {name} from shanks (idx {s_map[name]}) -> {target_id} ({np.sum(mask)} voxels)")

        del t_arr, s_arr; gc.collect()

        bone_mask = combined_arr > 0
        if not np.any(bone_mask):
            raise ValueError("Combined segmentation has no non-zero labels!")

        # --- 3. Find Bounding Box in Segmentation Array Space ---
        logging.info("Finding bounding box in segmentation space...")
        z_idx, y_idx, x_idx = np.where(bone_mask)
        z_min_i, z_max_i = int(z_idx.min()), int(z_idx.max()) + 1
        y_min_i, y_max_i = int(y_idx.min()), int(y_idx.max()) + 1
        x_min_i, x_max_i = int(x_idx.min()), int(x_idx.max()) + 1

        t_img = sitk.ReadImage(str(args.thighs_seg))
        spacing = t_img.GetSpacing()
        margin_vox = [int(args.margin_mm / s) for s in spacing]
        
        x_min_i = max(0, x_min_i - margin_vox[0]); x_max_i = min(combined_arr.shape[2], x_max_i + margin_vox[0])
        y_min_i = max(0, y_min_i - margin_vox[1]); y_max_i = min(combined_arr.shape[1], y_max_i + margin_vox[1])
        z_min_i = max(0, z_min_i - margin_vox[2]); z_max_i = min(combined_arr.shape[0], z_max_i + margin_vox[2])

        seg_crop_arr = combined_arr[z_min_i:z_max_i, y_min_i:y_max_i, x_min_i:x_max_i]
        del combined_arr, bone_mask; gc.collect()

        seg_crop = sitk.GetImageFromArray(seg_crop_arr)
        crop_origin = t_img.TransformIndexToPhysicalPoint((x_min_i, y_min_i, z_min_i))
        seg_crop.SetSpacing(spacing)
        seg_crop.SetDirection(t_img.GetDirection())
        seg_crop.SetOrigin(crop_origin)
        del t_img; gc.collect()

        # --- 4. Read the Cropped CT ---
        logging.info("Reading cropped CT via inverse transform...")
        inverse_tx = tx.GetInverse()
        
        crop_size = seg_crop.GetSize()
        corners_idx = [
            (0, 0, 0), (crop_size[0]-1, 0, 0), (0, crop_size[1]-1, 0), (0, 0, crop_size[2]-1),
            (crop_size[0]-1, crop_size[1]-1, 0), (crop_size[0]-1, 0, crop_size[2]-1),
            (0, crop_size[1]-1, crop_size[2]-1), (crop_size[0]-1, crop_size[1]-1, crop_size[2]-1),
        ]
        
        raw_corners = []
        for c in corners_idx:
            world = seg_crop.TransformIndexToPhysicalPoint(c)
            raw_corners.append(inverse_tx.TransformPoint(world))

        rx_min = min(c[0] for c in raw_corners); rx_max = max(c[0] for c in raw_corners)
        ry_min = min(c[1] for c in raw_corners); ry_max = max(c[1] for c in raw_corners)
        rz_min = min(c[2] for c in raw_corners); rz_max = max(c[2] for c in raw_corners)

        ct_reader = sitk.ImageFileReader()
        ct_reader.SetFileName(str(args.ct))
        ct_reader.ReadImageInformation()

        ct_ref = sitk.Image(ct_reader.GetSize(), sitk.sitkUInt8)
        ct_ref.SetOrigin(ct_reader.GetOrigin())
        ct_ref.SetSpacing(ct_reader.GetSpacing())
        ct_ref.SetDirection(ct_reader.GetDirection())

        raw_i_min = ct_ref.TransformPhysicalPointToIndex((rx_min, ry_min, rz_min))
        raw_i_max = ct_ref.TransformPhysicalPointToIndex((rx_max, ry_max, rz_max))

        img_size = ct_reader.GetSize()
        raw_x0 = max(0, raw_i_min[0]); raw_x1 = min(img_size[0], raw_i_max[0] + 1)
        raw_y0 = max(0, raw_i_min[1]); raw_y1 = min(img_size[1], raw_i_max[1] + 1)
        raw_z0 = max(0, raw_i_min[2]); raw_z1 = min(img_size[2], raw_i_max[2] + 1)

        ct_reader.SetExtractIndex((raw_x0, raw_y0, raw_z0))
        ct_reader.SetExtractSize((raw_x1 - raw_x0, raw_y1 - raw_y0, raw_z1 - raw_z0))
        ct_raw = ct_reader.Execute()
        del ct_ref; gc.collect()

        # --- 5. Apply Transform to Cropped CT ---
        logging.info("Applying transform to cropped CT...")
        ct_final = sitk.Resample(ct_raw, seg_crop, tx, sitk.sitkLinear, 0.0, ct_raw.GetPixelID())
        del ct_raw; gc.collect()

        # --- 6. Center Patient at X=0 (Robust Physical Math) ---
        logging.info("Centering patient at X=0...")
        seg_arr_final = sitk.GetArrayFromImage(seg_crop)
        zi_R, yi_R, xi_R = np.where(seg_arr_final == 1)
        zi_L, yi_L, xi_L = np.where(seg_arr_final == 2)
        
        if len(xi_R) > 0 and len(xi_L) > 0:
            # Convert array indices to physical coordinates (handles the -1 direction automatically)
            c_R = seg_crop.TransformContinuousIndexToPhysicalPoint((xi_R.mean(), yi_R.mean(), zi_R.mean()))
            c_L = seg_crop.TransformContinuousIndexToPhysicalPoint((xi_L.mean(), yi_L.mean(), zi_L.mean()))
            
            mid_world_x = (c_R[0] + c_L[0]) / 2.0
            shift = -mid_world_x
            
            current_origin = seg_crop.GetOrigin()
            new_origin = (current_origin[0] + shift, current_origin[1], current_origin[2])
            
            ct_final.SetOrigin(new_origin)
            seg_crop.SetOrigin(new_origin)
            logging.info(f"Shifted X by {shift:+.1f} mm to center patient.")
        else:
            logging.warning("Could not find both femurs to center. Skipping centering.")

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