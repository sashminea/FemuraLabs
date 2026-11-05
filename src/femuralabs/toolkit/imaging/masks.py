"""Extract per-bone binary masks, volumes, and centroids from a labelled volume."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import ndimage as ndi

from femuralabs.toolkit.fileio.volume import Volume


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
    volume_filled_ml: float                       # Volume if the interior holes are filled
    centroid_world: tuple[float, float, float]    # LPS millimetres


def fill_bone_interior(mask: np.ndarray) -> np.ndarray:
    """Fill the unlabeled interior of a cortical-shell mask, one axial slice (axis 0) at a time."""
    boxes = ndi.find_objects(mask.astype(np.uint8))
    if not boxes or boxes[0] is None:
        return mask.copy()
    box = boxes[0]
    out = mask.copy()
    # Iterate over each axial slice in the bounding box to fill holes
    out[box] = np.stack([ndi.binary_fill_holes(s) for s in mask[box]])
    return out


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
            volume_filled_ml = 0.0
            centroid_world = (float("nan"), float("nan"), float("nan"))
        else:
            volume_ml = count * voxel_volume_mm3 / 1000.0
            
            # Calculate the filled volume
            filled_mask = fill_bone_interior(mask)
            filled_count = int(filled_mask.sum())
            volume_filled_ml = filled_count * voxel_volume_mm3 / 1000.0

            # Centroid in array order (z, y, x).
            z_i, y_i, x_i = np.argwhere(mask).mean(axis=0)
            # Reorder to (x, y, z) to match spacing, origin, direction.
            centroid_xyz = np.array([x_i, y_i, z_i])
            world = origin + D @ (np.array(volume.spacing) * centroid_xyz)
            centroid_world = tuple(float(v) for v in world)
            
        result[name] = BoneMask(
            label, name, mask, count, volume_ml, volume_filled_ml, centroid_world
        )
    return result