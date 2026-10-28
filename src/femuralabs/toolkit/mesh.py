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
        padded, level=0.5, spacing=(sz, sy, sx),
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

def signed_volume(verts: np.ndarray, faces: np.ndarray) -> float:
    """Signed volume of a closed mesh, in the units of verts cubed.

    Sum of tetrahedron volumes from the origin. Positive for an
    outward-wound closed mesh; the absolute value is the physical volume.
    """
    v0 = verts[faces[:, 0]]
    v1 = verts[faces[:, 1]]
    v2 = verts[faces[:, 2]]
    return float(np.sum(v0 * np.cross(v1, v2)) / 6.0)


def edge_incidence(verts: np.ndarray, faces: np.ndarray) -> dict[str, int]:
    """Count edges by number of faces sharing them.

    A marching-cubes mesh is closed (every edge shared by 2 faces) in the
    ideal case. In practice, skimage's algorithm produces a handful of
    non-manifold edges (count 3) where two surface patches touch at an
    edge. The signed volume stays well-defined as long as boundary edges
    (count 1) are zero.
    """
    edges = np.sort(
        np.concatenate([faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]]),
        axis=1,
    )
    keys = edges[:, 0].astype(np.int64) * len(verts) + edges[:, 1].astype(np.int64)
    _, counts = np.unique(keys, return_counts=True)
    return {
        "boundary": int((counts == 1).sum()),
        "manifold": int((counts == 2).sum()),
        "non_manifold": int((counts >= 3).sum()),
    }


def is_watertight(verts: np.ndarray, faces: np.ndarray, tol: float = 0.001) -> bool:
    """True if the mesh has no open boundary and only negligible
    non-manifold edges (fewer than tol fraction of faces)."""
    counts = edge_incidence(verts, faces)
    return (
        counts["boundary"] == 0
        and counts["non_manifold"] / max(len(faces), 1) < tol
    )


def read_stl_vertices(path: Path | str) -> np.ndarray:
    """Parse an ASCII STL and return all vertex positions as (N, 3).

    Every face contributes 3 vertices, so N == 3 * n_faces. Duplicated
    vertices at shared corners are kept, because the STL format does not
    share them.
    """
    verts = []
    with open(str(path)) as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) == 4 and parts[0] == "vertex":
                verts.append([float(parts[1]), float(parts[2]), float(parts[3])])
    return np.array(verts)