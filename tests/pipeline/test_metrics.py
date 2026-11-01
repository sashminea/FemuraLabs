"""Tests for Dice and HD95."""
import numpy as np
import pytest

from femuralabs.toolkit.geometry.metrics import dice_score, iou_score, hd95


def test_dice_and_iou_perfect_overlap():
    a = np.zeros((10, 10, 10), dtype=bool)
    a[2:6, 2:6, 2:6] = True
    assert dice_score(a, a) == 1.0
    assert iou_score(a, a) == 1.0


def test_dice_and_iou_no_overlap():
    a = np.zeros((10, 10, 10), dtype=bool)
    a[2:5, 2:5, 2:5] = True
    b = np.zeros((10, 10, 10), dtype=bool)
    b[6:9, 6:9, 6:9] = True
    assert dice_score(a, b) == 0.0
    assert iou_score(a, b) == 0.0


def test_dice_hand_example():
    # Prediction 50 voxels, Reference 40, overlap 30
    # Dice = 2*30 / (50+40) = 60/90 = 0.667
    # IoU = 30 / (50+40-30) = 30/60 = 0.5
    # We can simulate this with a small array where we manually count
    # Or just trust the formula logic if the above tests pass.
    # Let's do a tiny 3D array.
    a = np.zeros((10,), dtype=bool) # 1D for simplicity
    b = np.zeros((10,), dtype=bool)
    
    # A has 5 elements, B has 4 elements, overlap is 3.
    a[0:5] = True
    b[2:6] = True
    # Intersection: indices 2,3,4 (3 elements)
    # Union: indices 0,1,2,3,4,5 (6 elements)
    
    assert dice_score(a, b) == pytest.approx(2*3 / (5+4))
    assert iou_score(a, b) == pytest.approx(3 / 6)


def test_hd95_identical_masks():
    a = np.zeros((10, 10, 10), dtype=bool)
    a[2:6, 2:6, 2:6] = True
    assert hd95(a, a, spacing=(1.0, 1.0, 1.0)) == 0.0


def test_hd95_single_voxel_offset():
    a = np.zeros((10, 10, 10), dtype=bool)
    a[2, 2, 2] = True
    b = np.zeros((10, 10, 10), dtype=bool)
    b[2, 2, 5] = True  # 3 voxels away along z
    
    # The surface distance is just the distance between these two voxels.
    # With spacing (1,1,1), distance is 3.0 mm.
    # Since it's symmetric and there's only one distance, the 95th percentile is 3.0
    assert hd95(a, b, spacing=(1.0, 1.0, 1.0)) == pytest.approx(3.0)


def test_hd95_spacing_applied():
    a = np.zeros((10, 10, 10), dtype=bool)
    a[2, 2, 2] = True
    b = np.zeros((10, 10, 10), dtype=bool)
    b[2, 2, 5] = True  # 3 voxels away along z
    
    # If spacing is 2.0 in z, distance is 3 * 2.0 = 6.0 mm
    assert hd95(a, b, spacing=(1.0, 1.0, 2.0)) == pytest.approx(6.0)