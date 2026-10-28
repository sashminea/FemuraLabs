"""Tests for mask_to_mesh."""
from pathlib import Path

import numpy as np
import pytest

from femuralabs.toolkit.io_volume import load_volume
from femuralabs.toolkit.masks import extract_masks
from femuralabs.toolkit.mesh import mask_to_mesh


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