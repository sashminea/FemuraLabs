"""Overlap and surface-distance metrics for segmentation comparison."""
from __future__ import annotations

import numpy as np
from scipy import ndimage
from scipy.spatial import cKDTree

def dice_score(mask_a: np.ndarray, mask_b: np.ndarray) -> float:
    """Dice similarity coefficient (0 to 1). 1 means perfect overlap."""
    intersection = np.logical_and(mask_a, mask_b).sum()
    if mask_a.sum() == 0 and mask_b.sum() == 0:
        return 1.0
    return float(2.0 * intersection / (mask_a.sum() + mask_b.sum()))


def iou_score(mask_a: np.ndarray, mask_b: np.ndarray) -> float:
    """Intersection over Union (Jaccard index), 0 to 1."""
    intersection = np.logical_and(mask_a, mask_b).sum()
    union = np.logical_or(mask_a, mask_b).sum()
    if union == 0:
        return 1.0
    return float(intersection / union)


from scipy.spatial import cKDTree

def _surface_distances(mask_a, mask_b, spacing):
    """Distances (mm) from the surface of mask_a to the nearest surface voxel of mask_b.

    Arrays are (z, y, x) but `spacing` is (x, y, z), so reverse it before scaling.
    """
    sp_zyx = np.asarray(spacing, dtype=float)[::-1]
    struct = ndimage.generate_binary_structure(3, 1)
    surf_a = mask_a & ~ndimage.binary_erosion(mask_a, struct)
    surf_b = mask_b & ~ndimage.binary_erosion(mask_b, struct)
    coords_a = np.argwhere(surf_a) * sp_zyx
    coords_b = np.argwhere(surf_b) * sp_zyx
    if len(coords_b) == 0:
        return np.array([float("inf")])
    dists, _ = cKDTree(coords_b).query(coords_a)
    return dists

def hd95(mask_a: np.ndarray, mask_b: np.ndarray, spacing: tuple[float, float, float]) -> float:
    """95th percentile Hausdorff Distance in mm."""
    if not np.any(mask_a) and not np.any(mask_b):
        return 0.0
    if not np.any(mask_a) or not np.any(mask_b):
        return float("inf")
        
    dists_a_to_b = _surface_distances(mask_a, mask_b, spacing)
    dists_b_to_a = _surface_distances(mask_b, mask_a, spacing)
    
    all_dists = np.concatenate([dists_a_to_b, dists_b_to_a])
    return float(np.percentile(all_dists, 95))