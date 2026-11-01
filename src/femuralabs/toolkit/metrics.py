"""Overlap and surface-distance metrics for segmentation comparison."""
from __future__ import annotations

import numpy as np
from scipy import ndimage


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


def _surface_distances(mask_a: np.ndarray, mask_b: np.ndarray, spacing: tuple[float, float, float]) -> np.ndarray:
    """Distances from the surface of mask_a to the nearest surface voxel of mask_b."""
    # Extract surface voxels (mask minus its erosion)
    struct = ndimage.generate_binary_structure(3, 1)
    surface_a = mask_a & ~ndimage.binary_erosion(mask_a, struct)
    
    # Distance transform of the inverted mask_b
    # (This gives the distance from any voxel to the closest mask_b voxel)
    dt_b = ndimage.distance_transform_edt(~mask_b, sampling=spacing)
    
    # Read the distances at the surface_a voxels
    return dt_b[surface_a]


def hd95(mask_a: np.ndarray, mask_b: np.ndarray, spacing: tuple[float, float, float]) -> float:
    """95th percentile Hausdorff Distance in mm.

    Computes the surface distances in both directions, pools them,
    and takes the 95th percentile. This is the standard medical imaging
    definition (e.g., as implemented in MONAI or medpy).
    """
    if not np.any(mask_a) and not np.any(mask_b):
        return 0.0
    if not np.any(mask_a) or not np.any(mask_b):
        return float("inf")
        
    # Distances from A surface to B, and B surface to A
    dists_a_to_b = _surface_distances(mask_a, mask_b, spacing)
    dists_b_to_a = _surface_distances(mask_b, mask_a, spacing)
    
    # Pool the distances and take the 95th percentile
    all_dists = np.concatenate([dists_a_to_b, dists_b_to_a])
    return float(np.percentile(all_dists, 95))