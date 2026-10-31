"""Extract per-bone binary masks, volumes, and centroids from a labelled volume."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from femuralabs.toolkit.io_volume import Volume


LABEL_NAMES = {
    1: "femur_R",
    2: "femur_L",
    3: "tibia_R",
    4: "tibia_L",
    5: "fibula_R",
    6: "fibula_L",
    7: "talus_R",
    8: "talus_L",
}


@dataclass(frozen=True)
class BoneMask:
    """A single bone: source label, boolean mask, volume in mL, centroid in LPS mm."""
    label: int
    name: str
    mask: np.ndarray                              # bool, same shape as source volume
    voxel_count: int
    volume_ml: float
    centroid_world: tuple[float, float, float]    # LPS millimetres


def extract_masks(volume: Volume) -> dict[str, BoneMask]:
    """Return one BoneMask per bone present in a combined segmentation.

    The label numbers are the ones written by the merge step; see
    docs/data.md. The centroid is the mean of the bone's voxel indices,
    mapped to LPS world coordinates with the same affine the volume
    carries: world = origin + direction @ (spacing * index). This makes
    the result comparable across subjects.
    """
    sx, sy, sz = volume.spacing
    voxel_volume_mm3 = sx * sy * sz
    D = np.array(volume.direction).reshape(3, 3)
    origin = np.array(volume.origin)

    result: dict[str, BoneMask] = {}
    for label, name in LABEL_NAMES.items():
        mask = volume.array == label
        count = int(mask.sum())
        if count == 0:
            volume_ml = 0.0
            centroid_world = (float("nan"), float("nan"), float("nan"))
        else:
            volume_ml = count * voxel_volume_mm3 / 1000.0
            # Centroid in array order (z, y, x).
            z_i, y_i, x_i = np.argwhere(mask).mean(axis=0)
            # Reorder to (x, y, z) to match spacing, origin, direction.
            centroid_xyz = np.array([x_i, y_i, z_i])
            world = origin + D @ (np.array(volume.spacing) * centroid_xyz)
            centroid_world = tuple(float(v) for v in world)
        result[name] = BoneMask(label, name, mask, count, volume_ml, centroid_world)
    return result