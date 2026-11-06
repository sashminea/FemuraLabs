#!/usr/bin/env python3
"""Prepare full-volume training data for the bone segmentation model.

Reads a manifest JSON that maps each case name to its CT and seg files:
    {
      "case01": {"ct": "/path/to/ct.nrrd", "seg": "data/raw/case01/combined_seg.nii"},
      ...
    }

Then for each case:
  1. fills the hollow (cortical-shell) bone labels at NATIVE resolution,
  2. resamples labels (nearest neighbour) and CT (linear) onto an isotropic grid,
  3. saves  <out>/<case>_ct.npy   int16, raw HU, array order (z, y, x)
            <out>/<case>_seg.npy  uint8, the 8 original labels (sides NOT merged)
            <out>/<case>_meta.json  native and resampled geometry.

Run:
    PYTHONPATH=src python scripts/ml/prepare_dataset.py --manifest scripts/ml/manifest.json
"""
from __future__ import annotations

import argparse
import gc
import json
from pathlib import Path

import numpy as np
import SimpleITK as sitk

from femuralabs.toolkit.imaging.masks import LABEL_NAMES, fill_bone_interior

HU_AIR = -1024.0  # value used outside the original field of view


def read_header(path: Path | str) -> dict:
    reader = sitk.ImageFileReader()
    reader.SetFileName(str(path))
    reader.ReadImageInformation()
    return {
        "size": tuple(int(s) for s in reader.GetSize()),
        "spacing": tuple(float(s) for s in reader.GetSpacing()),
        "origin": tuple(float(o) for o in reader.GetOrigin()),
        "direction": tuple(float(d) for d in reader.GetDirection()),
    }


def check_geometry(ct_h: dict, seg_h: dict, case: str) -> None:
    if ct_h["size"] != seg_h["size"]:
        raise ValueError(f"{case}: CT size {ct_h['size']} != seg size {seg_h['size']}")
    for key, tol in (("spacing", 1e-4), ("origin", 1e-3), ("direction", 1e-4)):
        if not np.allclose(ct_h[key], seg_h[key], atol=tol):
            raise ValueError(f"{case}: CT and seg differ in {key}: {ct_h[key]} vs {seg_h[key]}")
    if not np.allclose(ct_h["direction"], np.eye(3).ravel(), atol=1e-4):
        raise ValueError(f"{case}: direction is not identity. Reorientation not implemented.")


def target_grid(header: dict, spacing_mm: float):
    old_sp = np.array(header["spacing"])
    old_size = np.array(header["size"])
    direction = np.array(header["direction"]).reshape(3, 3)
    new_sp = np.full(3, float(spacing_mm))
    new_size = np.ceil(old_size * old_sp / new_sp - 1e-6).astype(int)
    new_origin = np.array(header["origin"]) + direction @ (0.5 * (new_sp - old_sp))
    return (
        tuple(int(s) for s in new_size),
        tuple(float(s) for s in new_sp),
        tuple(float(o) for o in new_origin),
        tuple(float(d) for d in header["direction"]),
    )


def make_reference(size, spacing, origin, direction) -> sitk.Image:
    ref = sitk.Image(list(size), sitk.sitkUInt8)
    ref.SetSpacing(spacing)
    ref.SetOrigin(origin)
    ref.SetDirection(direction)
    return ref


def count_labels(arr: np.ndarray, n: int = 9) -> np.ndarray:
    counts = np.zeros(n, dtype=np.int64)
    for z0 in range(0, arr.shape[0], 128):
        counts += np.bincount(arr[z0:z0 + 128].ravel(), minlength=n)[:n]
    return counts


def fill_labels(seg_arr: np.ndarray) -> tuple[np.ndarray, dict]:
    out = seg_arr.copy()
    added: dict[str, int] = {}
    for label, name in LABEL_NAMES.items():
        mask = seg_arr == label
        if not mask.any():
            added[name] = 0
            continue
        filled = fill_bone_interior(mask)
        new = filled & ~mask & (out == 0)
        added[name] = int(new.sum())
        out[new] = label
        del mask, filled, new
        gc.collect()
    return out, added


def process_case(case: str, ct_path: str, seg_path: str, out_dir: Path,
                 spacing_mm: float, overwrite: bool) -> None:
    ct_out = out_dir / f"{case}_ct.npy"
    seg_out = out_dir / f"{case}_seg.npy"
    meta_out = out_dir / f"{case}_meta.json"
    
    if not overwrite and ct_out.exists() and seg_out.exists() and meta_out.exists():
        print(f"{case}: outputs exist, skipping (use --overwrite to redo)")
        return
    if not Path(ct_path).exists() or not Path(seg_path).exists():
        print(f"{case}: missing CT or seg, skipping ({ct_path}, {seg_path})")
        return

    print(f"{case}: reading headers", flush=True)
    ct_h, seg_h = read_header(ct_path), read_header(seg_path)
    check_geometry(ct_h, seg_h, case)
    size, spacing, origin, direction = target_grid(seg_h, spacing_mm)
    ref = make_reference(size, spacing, origin, direction)
    identity = sitk.Transform(3, sitk.sitkIdentity)

    print(f"{case}: filling bone interiors at native resolution", flush=True)
    seg_img = sitk.ReadImage(str(seg_path))
    seg_arr = sitk.GetArrayFromImage(seg_img)
    del seg_img
    if seg_arr.dtype != np.uint8:
        raise ValueError(f"{case}: seg dtype {seg_arr.dtype}, expected uint8")
    if seg_arr.max() > 8:
        raise ValueError(f"{case}: seg has labels above 8")
    filled, added = fill_labels(seg_arr)
    del seg_arr
    gc.collect()
    native_counts = count_labels(filled)

    print(f"{case}: resampling labels to {spacing_mm} mm", flush=True)
    lab_img = sitk.GetImageFromArray(filled)
    lab_img.SetSpacing(seg_h["spacing"])
    lab_img.SetOrigin(seg_h["origin"])
    lab_img.SetDirection(seg_h["direction"])
    del filled
    gc.collect()
    lab_rs = sitk.Resample(lab_img, ref, identity, sitk.sitkNearestNeighbor, 0, sitk.sitkUInt8)
    del lab_img
    seg_new = sitk.GetArrayFromImage(lab_rs).astype(np.uint8, copy=False)
    del lab_rs
    new_counts = count_labels(seg_new)

    print(f"{case}: resampling CT", flush=True)
    ct_img = sitk.ReadImage(str(ct_path))
    ct_rs = sitk.Resample(ct_img, ref, identity, sitk.sitkLinear, HU_AIR, sitk.sitkFloat32)
    del ct_img
    gc.collect()
    ct_arr = sitk.GetArrayFromImage(ct_rs)
    del ct_rs
    np.rint(ct_arr, out=ct_arr)
    np.clip(ct_arr, -32768, 32767, out=ct_arr)
    ct_i16 = ct_arr.astype(np.int16)
    del ct_arr
    gc.collect()

    out_dir.mkdir(parents=True, exist_ok=True)
    np.save(ct_out, ct_i16)
    np.save(seg_out, seg_new)
    
    old_vox_ml = float(np.prod(seg_h["spacing"])) / 1000.0
    new_vox_ml = float(np.prod(spacing)) / 1000.0
    volumes = {}
    for label, name in LABEL_NAMES.items():
        volumes[name] = {
            "native_filled_ml": round(float(native_counts[label]) * old_vox_ml, 2),
            "resampled_ml": round(float(new_counts[label]) * new_vox_ml, 2),
            "voxels_added_by_fill": added[name],
        }
    meta = {
        "case": case,
        "spacing_mm": spacing_mm,
        "native": seg_h,
        "resampled": {"size": size, "spacing": spacing, "origin": origin, "direction": direction},
        "array_order": "z, y, x (numpy); SimpleITK size is x, y, z",
        "ct_dtype": "int16 raw HU", "seg_dtype": "uint8 original labels 0-8 (filled)",
        "volumes_ml": volumes,
    }
    meta_out.write_text(json.dumps(meta, indent=2))

    rel = [abs(v["resampled_ml"] - v["native_filled_ml"]) / max(v["native_filled_ml"], 1e-9)
           for v in volumes.values() if v["native_filled_ml"] > 0]
    pcts = np.percentile(ct_i16[::2, ::2, ::2], [1, 50, 99])
    print(f"{case}: saved ct {ct_i16.shape} {ct_i16.dtype}, seg {seg_new.shape} {seg_new.dtype}; "
          f"HU p1/p50/p99 = {pcts.round(0).tolist()}; "
          f"max label-volume change = {100 * max(rel):.1f}%", flush=True)
    del ct_i16, seg_new
    gc.collect()


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--manifest", type=Path, required=True, help="JSON mapping case names to ct/seg paths")
    p.add_argument("--out", type=Path, default=Path("data/ml_npy"))
    p.add_argument("--spacing", type=float, default=1.5, help="isotropic spacing in mm")
    p.add_argument("--cases", nargs="*", default=None, help="subset of cases to process (default: all in manifest)")
    p.add_argument("--overwrite", action="store_true")
    args = p.parse_args(argv)

    if not args.manifest.exists():
        raise SystemExit(f"manifest not found: {args.manifest}")

    manifest = json.loads(args.manifest.read_text())
    cases_to_run = args.cases if args.cases else list(manifest.keys())

    for case in cases_to_run:
        if case not in manifest:
            print(f"WARNING: {case} not in manifest, skipping")
            continue
        entry = manifest[case]
        process_case(case, entry["ct"], entry["seg"], args.out, args.spacing, args.overwrite)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())