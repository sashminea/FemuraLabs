"""Tests for mask_to_mesh."""
from pathlib import Path

import numpy as np
import pytest

from femuralabs.toolkit.io_volume import load_volume
from femuralabs.toolkit.masks import extract_masks
from femuralabs.toolkit.mesh import mask_to_mesh, read_stl_vertices, is_watertight, save_stl, signed_volume, edge_incidence

COMBINED = Path("data/raw/case01/combined_seg.nii")


def test_cube_mesh_has_correct_size_and_centre():
    """A 5-voxel cube at spacing 1 makes a 5 mm cube centred at (5, 5, 5)."""
    mask = np.zeros((10, 10, 10), dtype=bool)
    mask[3:8, 3:8, 3:8] = True
    verts, faces = mask_to_mesh(
        mask,
        spacing=(1.0, 1.0, 1.0),
        origin=(0.0, 0.0, 0.0),
        direction=(1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0),
    )
    assert len(faces) > 0
    extents = verts.max(axis=0) - verts.min(axis=0)
    assert np.allclose(extents, 5.0, atol=1e-6)
    assert np.allclose(verts.mean(axis=0), (5.0, 5.0, 5.0), atol=0.5)


@pytest.fixture(scope="module")
def real_case():
    if not COMBINED.exists():
        pytest.skip("combined_seg.nii missing")
    volume = load_volume(COMBINED)
    return volume, extract_masks(volume)


def test_femur_mesh_is_near_mask_centroid(real_case):
    """The surface-centroid should be within 20 mm of the volume-centroid.

    A dropped direction matrix or a missed (z,y,x) reorder would move
    the femur by ~167 mm in x; a small offset is surface-vs-volume bias.
    """
    volume, masks = real_case
    verts, faces = mask_to_mesh(
        masks["femur_R"].mask,
        spacing=volume.spacing,
        origin=volume.origin,
        direction=volume.direction,
    )
    assert len(verts) > 1000
    mesh_centroid = verts.mean(axis=0)
    mask_centroid = np.array(masks["femur_R"].centroid_world)
    assert np.allclose(mesh_centroid, mask_centroid, atol=20.0), (
        f"mesh {mesh_centroid} vs mask {mask_centroid}"
    )

def test_cube_mesh_is_watertight():
    mask = np.zeros((10, 10, 10), dtype=bool)
    mask[3:8, 3:8, 3:8] = True
    verts, faces = mask_to_mesh(
        mask, (1.0, 1.0, 1.0), (0.0, 0.0, 0.0),
        (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0),
    )
    counts = edge_incidence(verts, faces)
    assert counts["boundary"] == 0
    assert counts["non_manifold"] == 0
    vol = abs(signed_volume(verts, faces))
    assert 110.0 < vol < 125.0, f"volume {vol} outside plausible chamfered range"

def test_signed_volume_on_explicit_cube():
    """Volume of a hand-built 12-triangle cube of side 5 is exactly 125."""
    verts = np.array([
        [0, 0, 0], [5, 0, 0], [5, 5, 0], [0, 5, 0],
        [0, 0, 5], [5, 0, 5], [5, 5, 5], [0, 5, 5],
    ], dtype=float)
    faces = np.array([
        [0, 2, 1], [0, 3, 2],   # bottom, -z
        [4, 5, 6], [4, 6, 7],   # top, +z
        [0, 1, 5], [0, 5, 4],   # front, -y
        [1, 2, 6], [1, 6, 5],   # right, +x
        [2, 3, 7], [2, 7, 6],   # back, +y
        [3, 0, 4], [3, 4, 7],   # left, -x
    ], dtype=int)
    counts = edge_incidence(verts, faces)
    assert counts["boundary"] == 0, f"open boundary: {counts}"
    assert counts["non_manifold"] == 0, f"non-manifold: {counts}"
    assert abs(signed_volume(verts, faces)) == pytest.approx(125.0, rel=1e-6)

def test_real_femur_mesh_volume_close_to_voxel_volume(real_case):
    """Mesh is closed (boundary edges = 0), volume within 10% of voxel count."""
    volume, masks = real_case
    verts, faces = mask_to_mesh(
        masks["femur_R"].mask, volume.spacing, volume.origin, volume.direction,
    )
    counts = edge_incidence(verts, faces)
    assert counts["boundary"] == 0, f"open boundary: {counts}"
    assert counts["non_manifold"] / len(faces) < 0.001, f"non-manifold: {counts}"
    mesh_vol = abs(signed_volume(verts, faces))
    voxel_vol = masks["femur_R"].volume_ml * 1000.0
    rel_error = abs(mesh_vol - voxel_vol) / voxel_vol
    assert rel_error < 0.10, (
        f"mesh {mesh_vol:.1f} vs voxel {voxel_vol:.1f} mm^3 ({rel_error:.3%}); "
        f"edges: {counts}"
    )

def test_stl_round_trip_preserves_bounding_box(tmp_path):
    mask = np.zeros((10, 10, 10), dtype=bool)
    mask[3:8, 3:8, 3:8] = True
    verts, faces = mask_to_mesh(
        mask, (1.0, 1.0, 1.0), (0.0, 0.0, 0.0),
        (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0),
    )
    path = tmp_path / "cube.stl"
    save_stl(path, verts, faces)
    verts_read = read_stl_vertices(path)
    assert len(verts_read) == len(faces) * 3
    assert np.allclose(verts_read.min(axis=0), verts.min(axis=0), atol=1e-5)
    assert np.allclose(verts_read.max(axis=0), verts.max(axis=0), atol=1e-5)

def test_empty_mask_returns_empty_mesh():
    """An all-False mask has no surface; the function returns empty arrays."""
    mask = np.zeros((10, 10, 10), dtype=bool)
    verts, faces = mask_to_mesh(
        mask, (1.0, 1.0, 1.0), (0.0, 0.0, 0.0),
        (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0),
    )
    assert len(verts) == 0
    assert len(faces) == 0