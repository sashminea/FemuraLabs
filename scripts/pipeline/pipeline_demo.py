"""End-to-end pipeline on one combined-segmentation case."""
from __future__ import annotations

import argparse
import gc
import json
from pathlib import Path

import numpy as np

from femuralabs.toolkit.fileio.volume import load_volume
from femuralabs.toolkit.imaging.masks import LABEL_NAMES, fill_bone_interior
from femuralabs.toolkit.imaging.mesh import mask_to_mesh, save_stl
from femuralabs.toolkit.geometry.landmarks import femoral_head_centre, knee_centre, ankle_centre
from femuralabs.toolkit.fileio.landmark import load_landmarks
from femuralabs.toolkit.geometry.alignment import (
    hka_deviation, hka_deviation_coronal, mad, mad_coronal, mldfa, mpta)

def run(case_path: Path, out_dir: Path, compare_path: Path | None = None,
        angles: bool = False, fill_interior: bool = False, knee_method: str = "box") -> dict:
    """Load, extract masks, mesh bones, return a summary dict."""
    print(f"Loading volume: {case_path}")
    volume = load_volume(case_path)
    out_dir.mkdir(parents=True, exist_ok=True)

    sx, sy, sz = volume.spacing
    voxel_volume_mm3 = sx * sy * sz

    bones: dict[str, dict] = {}
    verts_dict: dict[str, np.ndarray] = {}

    for label, name in LABEL_NAMES.items():
        print(f"  Extracting and meshing: {name}...", flush=True)
        mask = volume.array == label
        count = int(mask.sum())
        if count == 0:
            bones[name] = {
                "voxels": 0, "volume_ml": 0.0, "volume_filled_ml": 0.0,
                "vertices": 0, "faces": 0, "bbox_mm": None
            }
            continue

        volume_ml = count * voxel_volume_mm3 / 1000.0
        mesh_mask = fill_bone_interior(mask) if fill_interior else mask
        filled_count = int(mesh_mask.sum())
        volume_filled_ml = filled_count * voxel_volume_mm3 / 1000.0

        verts, faces = mask_to_mesh(mesh_mask, volume.spacing, volume.origin, volume.direction)
        verts_dict[name] = verts

        if len(verts) > 0:
            save_stl(out_dir / f"{name}.stl", verts, faces)
            bbox = [
                [round(float(v), 2) for v in verts.min(axis=0)],
                [round(float(v), 2) for v in verts.max(axis=0)],
            ]
        else:
            bbox = None

        bones[name] = {
            "voxels": int(count),
            "volume_ml": round(float(volume_ml), 2),
            "volume_filled_ml": round(float(volume_filled_ml), 2),
            "vertices": int(len(verts)),
            "faces": int(len(faces)),
            "bbox_mm": bbox,
        }
        del mask, mesh_mask, faces
        gc.collect()

    z, y, x = volume.array.shape
    summary = {
        "case": case_path.parent.name,
        "size": [int(x), int(y), int(z)],
        "spacing_mm": [round(float(s), 6) for s in volume.spacing],
        "origin_mm": [round(float(o), 6) for o in volume.origin],
        "bones": bones,
    }

    if compare_path:
        print(f"  Comparing against: {compare_path}", flush=True)
        hand = load_landmarks(compare_path)
        auto = {}
        for side in ("R", "L"):
            auto[f"femoral_head_{side}"] = femoral_head_centre(verts_dict[f"femur_{side}"])[0]
            auto[f"knee_centre_{side}"] = knee_centre(
                verts_dict[f"femur_{side}"], verts_dict[f"tibia_{side}"], method=knee_method
            )[0]
            auto[f"ankle_centre_{side}"] = ankle_centre(verts_dict[f"tibia_{side}"], verts_dict[f"fibula_{side}"])[0]

        summary["landmarks"] = {}
        for name in auto:
            if name in hand:
                err = float(np.linalg.norm(auto[name] - np.array(hand[name])))
                summary["landmarks"][name] = {
                    "auto": [round(float(v), 2) for v in auto[name]],
                    "hand": [round(float(v), 2) for v in hand[name]],
                    "error_mm": round(err, 2),
                    "delta_mm": [round(float(v), 2) for v in (auto[name] - np.array(hand[name]))],
                }

        if angles:
            print(f"  Computing angles...", flush=True)
            summary["angles"] = {}
            for side in ("R", "L"):
                hip_a  = auto[f"femoral_head_{side}"]
                knee_a = auto[f"knee_centre_{side}"]
                ankle_a = auto[f"ankle_centre_{side}"]
                hip_h  = np.array(hand[f"femoral_head_{side}"])
                knee_h = np.array(hand[f"knee_centre_{side}"])
                ankle_h = np.array(hand[f"ankle_centre_{side}"])

                def add_angle(name, a, h):
                    summary["angles"][name] = {
                        "auto": round(float(a), 2),
                        "hand": round(float(h), 2),
                        "diff_deg": round(float(a - h), 2),
                    }

                add_angle(f"HKA_{side}",
                        hka_deviation_coronal(hip_a, knee_a, ankle_a),
                        hka_deviation_coronal(hip_h, knee_h, ankle_h))
                add_angle(f"HKA3D_{side}",
                        hka_deviation(hip_a, knee_a, ankle_a),
                        hka_deviation(hip_h, knee_h, ankle_h))

                a_mad = mad_coronal(hip_a, knee_a, ankle_a)
                h_mad = mad_coronal(hip_h, knee_h, ankle_h)
                summary.setdefault("mad_mm", {})[side] = {
                    "auto": round(float(a_mad), 2), "hand": round(float(h_mad), 2),
                    "diff_mm": round(float(a_mad - h_mad), 2)}

                if all(f"{lm}_{side}" in hand for lm in
                       ("condyle_medial", "condyle_lateral", "plateau_medial", "plateau_lateral")):
                    c_med = np.array(hand[f"condyle_medial_{side}"])
                    c_lat = np.array(hand[f"condyle_lateral_{side}"])
                    p_med = np.array(hand[f"plateau_medial_{side}"])
                    p_lat = np.array(hand[f"plateau_lateral_{side}"])

                    add_angle(f"mLDFA_{side}",
                              mldfa(hip_a, knee_a, c_med, c_lat),
                              mldfa(hip_h, knee_h, c_med, c_lat))
                    add_angle(f"MPTA_{side}",
                              mpta(knee_a, ankle_a, p_med, p_lat),
                              mpta(knee_h, ankle_h, p_med, p_lat))

    return summary


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Run the pipeline on one case.")
    p.add_argument("--case", type=Path, required=True, help="path to a combined_seg.nii file")
    p.add_argument("--out", type=Path, required=True, help="output folder for STLs and summary.json")
    p.add_argument("--name", type=str, default=None, help="case name in the JSON")
    p.add_argument("--compare", type=Path, default=None, help="path to landmarks.mrk.json for comparison")
    p.add_argument("--angles", action="store_true", help="compute joint angles using hand landmarks where necessary")
    p.add_argument("--fill-interior", action="store_true", help="fill medullary canals before meshing")
    p.add_argument("--knee-method", type=str, default="box",
                   choices=["box", "condyle", "notch"], help="knee centre rule")
    args = p.parse_args(argv)

    summary = run(args.case, args.out, args.compare, args.angles, args.fill_interior, args.knee_method)
    if args.name:
        summary["case"] = args.name

    summary_path = args.out / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True))
    print(f"Wrote {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())