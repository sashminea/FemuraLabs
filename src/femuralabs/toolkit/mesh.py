"""Mask to mesh via marching cubes, in world millimetres."""
from __future__ import annotations

from pathlib import Path

import numpy as np
from skimage import measure


def mask_to_mesh(
    mask: np.ndarray,
    spacing: tuple[float, float, float],
    origin: tuple[float, float, float],
    direction: tuple[float, ...],
) -> tuple[np.ndarray, np.ndarray]:
    """Marching cubes on a boolean mask, transformed to LPS world coordinates.

    mask is (z, y, x), matching io_volume.Volume.array.
    spacing is (sx, sy, sz); origin is (x, y, z); direction is 9 floats
    row-major, as SimpleITK returns it.
    Returns (verts_world, faces): verts (N, 3) in LPS mm, faces (F, 3) int.
    """
    padded = np.pad(mask.astype(np.float32), 1, mode="constant", constant_values=0.0)

    # skimage expects spacing in array-axis order; array is (z, y, x).
    sz, sy, sx = spacing[2], spacing[1], spacing[0]
    verts_zyx, faces, _, _ = measure.marching_cubes(
        padded, level=0.5, spacing=(sz, sy, sx), allow_degenerate=False,
    )
    # Undo the 1-voxel padding that was added above.
    verts_zyx -= np.array([sz, sy, sx])
    # Reorder columns from (z, y, x) to (x, y, z).
    verts_xyz = verts_zyx[:, ::-1]
    # Apply direction and origin: world = origin + D @ vert_xyz, vectorised.
    D = np.asarray(direction, dtype=float).reshape(3, 3)
    verts_world = verts_xyz @ D.T + np.asarray(origin, dtype=float)
    return verts_world, faces


def save_stl(path: Path | str, verts: np.ndarray, faces: np.ndarray) -> None:
    """Write an ASCII STL. Units are whatever verts is in (here, mm)."""
    with open(str(path), "w") as f:
        f.write("solid mesh\n")
        for face in faces:
            v0, v1, v2 = verts[face[0]], verts[face[1]], verts[face[2]]
            n = np.cross(v1 - v0, v2 - v0)
            norm = np.linalg.norm(n)
            if norm > 0:
                n = n / norm
            f.write(f"  facet normal {n[0]:.6e} {n[1]:.6e} {n[2]:.6e}\n")
            f.write("    outer loop\n")
            for v in (v0, v1, v2):
                f.write(f"      vertex {v[0]:.6e} {v[1]:.6e} {v[2]:.6e}\n")
            f.write("    endloop\n")
            f.write("  endfacet\n")
        f.write("endsolid mesh\n")