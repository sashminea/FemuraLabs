"""Tests for volume I/O."""
from pathlib import Path

import numpy as np
import pytest

from femuralabs.toolkit.io_volume import Volume, load_volume, save_nifti


def test_identity_round_trip(tmp_path):
    """Identity direction survives write then read."""
    array = np.arange(4 * 5 * 6, dtype=np.float32).reshape(4, 5, 6)
    original = Volume(
        array=array,
        spacing=(1.5, 1.5, 2.0),
        origin=(-100.0, -120.0, 50.0),
        direction=(1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0),
    )
    path = tmp_path / "test.nii"
    save_nifti(original, path)
    reloaded = load_volume(path)

    assert np.array_equal(reloaded.array, array)
    assert reloaded.spacing == (1.5, 1.5, 2.0)
    assert reloaded.origin == (-100.0, -120.0, 50.0)
    assert reloaded.direction == (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)


def test_flipped_direction_round_trip(tmp_path):
    """A non-identity direction survives round trip unchanged.

    This is the direction of the case 01 combined segmentation; if
    SimpleITK normalises it away, this test fails.
    """
    array = np.zeros((3, 4, 5), dtype=np.float32)
    original = Volume(
        array=array,
        spacing=(1.0, 1.0, 3.0),
        origin=(0.0, 0.0, 0.0),
        direction=(-1.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0, 1.0),
    )
    path = tmp_path / "flipped.nii"
    save_nifti(original, path)
    reloaded = load_volume(path)

    assert reloaded.direction == (-1.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0, 1.0)


def test_real_file_array_shape():
    """The combined segmentation has array shape (z, y, x), not (x, y, z)."""
    path = Path("data/raw/case01/combined_seg.nii")
    if not path.exists():
        pytest.skip("combined_seg.nii not present; run the merge first")
    volume = load_volume(path)
    assert volume.array.shape == (1637, 512, 512)
    assert volume.spacing == pytest.approx(
        (0.9765625, 0.9765625, 0.6997554898262024)
    )