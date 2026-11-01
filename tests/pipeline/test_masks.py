"""Tests for bone mask extraction."""
from pathlib import Path

import numpy as np
import pytest

from femuralabs.toolkit.fileio.volume import load_volume
from femuralabs.toolkit.imaging.masks import LABEL_NAMES, extract_masks


COMBINED = Path("data/raw/case01/combined_seg.nii")


@pytest.fixture(scope="module")
def masks():
    if not COMBINED.exists():
        pytest.skip("combined_seg.nii missing; run the merge step first")
    return extract_masks(load_volume(COMBINED))


def test_all_four_bones_present(masks):
    for name in LABEL_NAMES.values():
        assert masks[name].voxel_count > 0, f"{name} has zero voxels"


def test_volume_matches_voxel_arithmetic(masks):
    """volume_ml == voxel_count * voxel_volume / 1000, recomputed from spacing."""
    volume = load_volume(COMBINED)
    sx, sy, sz = volume.spacing
    voxel_volume_mm3 = sx * sy * sz
    for m in masks.values():
        expected = m.voxel_count * voxel_volume_mm3 / 1000.0
        assert m.volume_ml == pytest.approx(expected, rel=1e-6)


def test_left_right_are_on_correct_sides(masks):
    """In LPS, the patient's left is +x.

    The direction matrix diag(-1, -1, 1) maps increasing array x-index to
    decreasing world x. So the patient's left femur has a HIGHER array
    x-index but a HIGHER world x. If the direction matrix were dropped
    (identity), this flips and the test fails — which is the point.
    """
    assert masks["femur_L"].centroid_world[0] > masks["femur_R"].centroid_world[0]
    assert masks["tibia_L"].centroid_world[0] > masks["tibia_R"].centroid_world[0]