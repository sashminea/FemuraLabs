"""End-to-end pipeline on one combined-segmentation case."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from femuralabs.toolkit.io_volume import load_volume
from femuralabs.toolkit.masks import extract_masks
from femuralabs.toolkit.mesh import mask_to_mesh, save_stl


def run(case_path: Path, out_dir: Path) -> dict:
    """Load, extract masks, mesh bones, return a summary dict.

    The dict is JSON-serialisable. Its numbers are deterministic — same
    input file, same output dict, no timestamps, no random state. That
    makes a diff between two runs of the same case meaningful.
    """
    volume = load_volume(case_path)
    masks = extract_masks(volume)
    out_dir.mkdir(parents=True, exist_ok=True)

    bones: dict[str, dict] = {}
    for name, bone in masks.items():
        verts, faces = mask_to_mesh(
            bone.mask, volume.spacing, volume.origin, volume.direction
        )
        if len(verts) > 0:
            save_stl(out_dir / f"{name}.stl", verts, faces)
            bbox = [
                [round(float(v), 2) for v in verts.min(axis=0)],
                [round(float(v), 2) for v in verts.max(axis=0)],
            ]
        else:
            bbox = None
        bones[name] = {
            "voxels": int(bone.voxel_count),
            "volume_ml": round(float(bone.volume_ml), 2),
            "vertices": int(len(verts)),
            "faces": int(len(faces)),
            "bbox_mm": bbox,
        }

    z, y, x = volume.array.shape
    return {
        "case": case_path.parent.name,
        "size": [int(x), int(y), int(z)],
        "spacing_mm": [round(float(s), 6) for s in volume.spacing],
        "origin_mm": [round(float(o), 6) for o in volume.origin],
        "bones": bones,
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Run the pipeline on one case.")
    p.add_argument("--case", type=Path, required=True,
                   help="path to a combined_seg.nii file")
    p.add_argument("--out", type=Path, required=True,
                   help="output folder for STLs and summary.json")
    p.add_argument("--name", type=str, default=None,
                   help="case name in the JSON (default: case file's parent folder)")
    args = p.parse_args(argv)

    summary = run(args.case, args.out)
    if args.name:
        summary["case"] = args.name

    summary_path = args.out / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True))
    print(f"wrote {summary_path}")
    for name, b in summary["bones"].items():
        print(f"  {name:<8}  {b['vertices']:>7} verts  {b['volume_ml']:>7.2f} mL")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())