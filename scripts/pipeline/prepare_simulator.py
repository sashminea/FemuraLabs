#!/usr/bin/env python3
"""
Generate simulator assets: femur, proximal tibia, distal tibia, and config.
Everything is in local coordinates centered at the knee (knee = origin).
"""
import argparse, json
from pathlib import Path
import numpy as np
import trimesh
from femuralabs.toolkit.fileio.volume import load_volume
from femuralabs.toolkit.fileio.landmark import load_landmarks
from femuralabs.toolkit.imaging.masks import extract_masks, fill_bone_interior
from femuralabs.toolkit.imaging.mesh import mask_to_mesh

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--case", default="case05")
    p.add_argument("--side", default="R", choices=["R","L"])
    p.add_argument("--out-dir", type=Path, default=Path("web/public/simulator"))
    p.add_argument("--cut-below-plateau-mm", type=float, default=15.0)
    p.add_argument("--decimate-femur", type=int, default=12000)
    p.add_argument("--decimate-tibia", type=int, default=10000)
    args = p.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading {args.case}...")
    vol = load_volume(f"data/raw/{args.case}/combined_seg.nii")
    masks = extract_masks(vol)
    lm = load_landmarks(f"data/ref/landmarks_{args.case}.mrk.json")
    S = args.side

    hip_w = np.array(lm[f"femoral_head_{S}"])
    knee_w = np.array(lm[f"knee_centre_{S}"])
    ankle_w = np.array(lm[f"ankle_centre_{S}"])
    pmed_w = np.array(lm[f"plateau_medial_{S}"])
    plat_w = np.array(lm[f"plateau_lateral_{S}"])

    print(f"Hip:   {hip_w.round(1)}")
    print(f"Knee:  {knee_w.round(1)}")
    print(f"Ankle: {ankle_w.round(1)}")

    # Meshes, filled, in world coords
    fverts, ffaces = mask_to_mesh(fill_bone_interior(masks[f"femur_{S}"].mask),
                                  vol.spacing, vol.origin, vol.direction)
    tverts, tfaces = mask_to_mesh(fill_bone_interior(masks[f"tibia_{S}"].mask),
                                  vol.spacing, vol.origin, vol.direction)
    print(f"Femur: {len(fverts):,} verts, {len(tfaces):,} tibia faces")

    z_top_tibia = float(tverts[:, 2].max())
    cut_z = z_top_tibia - args.cut_below_plateau_mm
    print(f"Cut plane z = {cut_z:.1f} mm (tibia top at {z_top_tibia:.1f})")

    # Cut band: hinge (lateral) and medial at cut
    band = tverts[np.abs(tverts[:, 2] - cut_z) < 3.0]
    if len(band) < 50:
        raise RuntimeError(f"Only {len(band)} verts at cut_z")
    width_at_cut = float(band[:, 0].max() - band[:, 0].min())
    print(f"Tibia width at cut: {width_at_cut:.1f} mm")
    if S == "R":
        hinge = band[int(np.argmin(band[:, 0]))].copy()
        medial_pt = band[int(np.argmax(band[:, 0]))].copy()
    else:
        hinge = band[int(np.argmax(band[:, 0]))].copy()
        medial_pt = band[int(np.argmin(band[:, 0]))].copy()
    print(f"Hinge: {hinge.round(1)}   Medial edge: {medial_pt.round(1)}")

    # Convert everything to knee-local coords
    knee = knee_w.copy()

    def to_local(p):
        v = np.array(p, dtype=float) - knee
        return [float(v[0]), float(v[1]), float(v[2])]

    hip_local = to_local(hip_w)
    ankle_local = to_local(ankle_w)
    hinge_local = to_local(hinge)
    medial_local = to_local(medial_pt)
    pmed_local = to_local(pmed_w)
    plat_local = to_local(plat_w)
    cut_z_local = float(cut_z - knee[2])

    # Translate meshes and export femur + tibia halves
    print("Building femur mesh...")
    fm = trimesh.Trimesh(vertices=fverts - knee, faces=ffaces, process=True)
    if len(fm.faces) > args.decimate_femur:
        fm = fm.simplify_quadric_decimation(face_count=args.decimate_femur)
    fm.export(str(args.out_dir / "femur.stl"), file_type="stl")
    print(f"Femur exported: {len(fm.faces):,} faces")

    print("Building tibia meshes...")
    tm = trimesh.Trimesh(vertices=tverts - knee, faces=tfaces, process=True)
    if len(tm.faces) > args.decimate_tibia:
        tm = tm.simplify_quadric_decimation(face_count=args.decimate_tibia)
    prox = tm.slice_plane(plane_origin=[0,0,cut_z_local], plane_normal=[0,0,1], cap=True)
    dist = tm.slice_plane(plane_origin=[0,0,cut_z_local], plane_normal=[0,0,-1], cap=True)
    prox.export(str(args.out_dir / "tibia_proximal.stl"), file_type="stl")
    dist.export(str(args.out_dir / "tibia_distal.stl"), file_type="stl")
    print(f"Tibia proximal: {len(prox.faces):,} faces")
    print(f"Tibia distal:   {len(dist.faces):,} faces")

    # Pre-op angles from summary
    summ = json.loads(Path(f"output/{args.case}/summary.json").read_text())
    pre_hka = float(summ["angles"][f"HKA_{S}"]["hand"])
    pre_mpta = float(summ["angles"].get(f"MPTA_{S}", {}).get("hand", 87.0))
    print(f"Pre-op HKA: {pre_hka:.2f}°  MPTA: {pre_mpta:.2f}°")

    cfg = {
        "case": args.case,
        "side": S,
        "hip_local": hip_local,
        "ankle_local": ankle_local,
        "hinge_local": hinge_local,
        "medial_edge_local": medial_local,
        "plateau_medial_local": pmed_local,
        "plateau_lateral_local": plat_local,
        "cut_plane_z_local": cut_z_local,
        "tibia_width_at_cut_mm": width_at_cut,
        "cut_below_plateau_mm": float(args.cut_below_plateau_mm),
        "pre_hka_deg": pre_hka,
        "pre_mpta_deg": pre_mpta,
    }
    (args.out_dir / "config.json").write_text(json.dumps(cfg, indent=2) + "\n")
    print(f"Wrote {args.out_dir}/config.json")

if __name__ == "__main__":
    main()
