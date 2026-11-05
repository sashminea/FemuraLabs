"""Landmark extraction from bone meshes."""
from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi
from skimage.morphology import convex_hull_image

# --- box rule constants ------------------------------------------------------
# The hand click sits at a fairly constant place relative to the x/y bounding
# box of a thin axial slab BOX_LEVEL_MM above the lowest femoral vertex.
# Offsets are means over the 16 knees (8 subjects) of the current hand
# reference; refit them if the reference changes.
BOX_LEVEL_MM = 15.0
BOX_THICKNESS_MM = 2.0
BOX_LATERAL_OFFSET_MM = 6.0     # click is this far lateral of the box centre
BOX_ANTERIOR_OFFSET_MM = 8.5    # click is this far anterior (smaller y in LPS)


def fit_sphere(points: np.ndarray) -> tuple[np.ndarray, float, float]:
    """Least-squares sphere fit."""
    if len(points) < 4:
        raise ValueError(f"Need at least 4 points, got {len(points)}")
    A = np.column_stack([
        2.0 * points[:, 0], 2.0 * points[:, 1], 2.0 * points[:, 2], np.ones(len(points))
    ])
    b = (points ** 2).sum(axis=1)
    sol, *_ = np.linalg.lstsq(A, b, rcond=None)
    a, bb, c, d = sol
    centre = np.array([a, bb, c])
    radius_sq = d + a * a + bb * bb + c * c
    if radius_sq <= 0:
        raise ValueError("Sphere fit produced non-positive radius squared")
    radius = float(np.sqrt(radius_sq))
    distances = np.linalg.norm(points - centre, axis=1)
    rms = float(np.sqrt(((distances - radius) ** 2).mean()))
    return centre, radius, rms


def femoral_head_centre(
    verts: np.ndarray, n_iter: int = 3, medial_window_mm: float = 20.0,
) -> tuple[np.ndarray, float, float]:
    """Estimate the femoral head centre from a femur mesh."""
    z = verts[:, 2]
    z_lo, z_hi = float(z.min()), float(z.max())
    cut = z_lo + 0.75 * (z_hi - z_lo)
    proximal = verts[z > cut]
    if len(proximal) < 100:
        raise ValueError(f"Proximal region has only {len(proximal)} vertices")
    median_x = float(np.median(verts[:, 0]))
    if median_x < 0:
        medial_x = float(proximal[:, 0].max())
        region = proximal[proximal[:, 0] > medial_x - medial_window_mm]
    else:
        medial_x = float(proximal[:, 0].min())
        region = proximal[proximal[:, 0] < medial_x + medial_window_mm]
    if len(region) < 50:
        raise ValueError(f"Medial window contains only {len(region)} vertices")
    current = region
    centre, radius, rms = fit_sphere(current)
    for _ in range(n_iter):
        distances = np.linalg.norm(current - centre, axis=1)
        residuals = np.abs(distances - radius)
        threshold = float(np.quantile(residuals, 0.8))
        kept = current[residuals <= threshold]
        if len(kept) < 50:
            break
        current = kept
        centre, radius, rms = fit_sphere(current)
    return centre, radius, rms


def _condyle_blobs(femur_verts, slab_mm):
    """Legacy two-blob rule: bottom slab split at its x mid-point."""
    fz_min = float(femur_verts[:, 2].min())
    slab = femur_verts[femur_verts[:, 2] < fz_min + slab_mm]
    if len(slab) < 100:
        raise ValueError(f"distal slab has only {len(slab)} verts")
    mid_x = (slab[:, 0].min() + slab[:, 0].max()) / 2.0
    half_a, half_b = slab[slab[:, 0] > mid_x], slab[slab[:, 0] < mid_x]
    if len(half_a) < 50 or len(half_b) < 50:
        raise ValueError(f"one condyle half has too few verts")
    a, b = half_a.mean(axis=0), half_b.mean(axis=0)
    right = float(np.median(femur_verts[:, 0])) < 0
    medial_is_a = (a[0] > b[0]) if right else (a[0] < b[0])
    medial, lateral = (a, b) if medial_is_a else (b, a)
    return (a + b) / 2.0, medial, lateral


def _notch_in_section(verts, z0, thickness_mm, px_mm=1.5, min_area_px=15):
    """Centre (x, y) in mm of the intercondylar gap in one axial slab."""
    sel = verts[(verts[:, 2] >= z0) & (verts[:, 2] < z0 + thickness_mm)]
    if len(sel) < 100:
        raise ValueError(f"only {len(sel)} verts in the section")
    pad = 4
    x0 = sel[:, 0].min() - pad * px_mm
    y0 = sel[:, 1].min() - pad * px_mm
    ix = np.floor((sel[:, 0] - x0) / px_mm).astype(int)
    iy = np.floor((sel[:, 1] - y0) / px_mm).astype(int)
    grid = np.zeros((iy.max() + pad + 1, ix.max() + pad + 1), bool)
    grid[iy, ix] = True
    solid = ndi.binary_fill_holes(ndi.binary_closing(grid, np.ones((3, 3), bool), iterations=2))

    gap = convex_hull_image(solid) & ~solid
    lab, n = ndi.label(gap)
    cols = np.where(solid.any(axis=0))[0]
    lo, hi = cols.min(), cols.max()
    best = None
    for k in range(1, n + 1):
        comp = lab == k
        area = int(comp.sum())
        cy, cx = ndi.center_of_mass(comp)
        in_middle = lo + 0.25 * (hi - lo) <= cx <= hi - 0.25 * (hi - lo)
        if area >= min_area_px and in_middle and (best is None or area > best[0]):
            best = (area, cx, cy)
    if best is None:
        raise ValueError("no notch-like gap")
    area, cx, cy = best
    return (x0 + (cx + 0.5) * px_mm, y0 + (cy + 0.5) * px_mm), area * px_mm ** 2


def _distal_femur_box(femur_verts, level_mm, thickness_mm):
    """(x_lo, x_hi), (y_lo, y_hi), n_verts of an axial slab above the lowest femur vertex."""
    z0 = float(femur_verts[:, 2].min()) + level_mm
    sel = femur_verts[(femur_verts[:, 2] >= z0) & (femur_verts[:, 2] < z0 + thickness_mm)]
    if len(sel) < 100:
        raise ValueError(f"only {len(sel)} femur verts in the box slab at +{level_mm} mm")
    return ((float(sel[:, 0].min()), float(sel[:, 0].max())),
            (float(sel[:, 1].min()), float(sel[:, 1].max())),
            len(sel))


def knee_centre(femur_verts, tibia_verts=None, method="box", level_mm=6.0,
                thickness_mm=2.0, slab_mm=5.0,
                box_level_mm=BOX_LEVEL_MM, box_thickness_mm=BOX_THICKNESS_MM):
    """Knee centre (x, y, z) in LPS mm.

    method="box" (default): x/y from the bounding box of the femur slab
        box_level_mm above its lowest vertex, shifted by the fitted lateral /
        anterior offsets; z = lowest vertex + level_mm. Does not depend on which
        condyle is lower. Offsets are fitted to the hand reference.
    method="condyle": legacy lowest-slab two-blob rule (fails when one condyle
        is more than slab_mm higher than the other).
    method="notch": legacy convex-hull gap rule (not validated).
    """
    if method not in ("box", "condyle", "notch"):
        raise ValueError(f"unknown knee_centre method {method!r}")
    if len(femur_verts) < 200:
        raise ValueError("too few femur verts")
    fz_min = float(femur_verts[:, 2].min())

    if method == "box":
        (x_lo, x_hi), (y_lo, y_hi), n_box = _distal_femur_box(
            femur_verts, box_level_mm, box_thickness_mm)
        right = float(np.median(femur_verts[:, 0])) < 0
        lateral_sign = -1.0 if right else 1.0          # LPS: +x is patient-left
        x = 0.5 * (x_lo + x_hi) + lateral_sign * BOX_LATERAL_OFFSET_MM
        y = 0.5 * (y_lo + y_hi) - BOX_ANTERIOR_OFFSET_MM
        try:
            blob_centre, medial, lateral = _condyle_blobs(femur_verts, slab_mm)
        except ValueError:
            blob_centre = medial = lateral = np.full(3, np.nan)
        return np.array([x, y, fz_min + level_mm]), {
            "condyle_medial": medial, "condyle_lateral": lateral, "slab_mm": float(slab_mm),
            "level_mm": float(level_mm), "notch_gap_mm2": 0.0,
            "centre_condyle_mid": blob_centre, "method": "box",
            "box_level_mm": float(box_level_mm),
            "box_x_range_mm": (x_lo, x_hi), "box_y_range_mm": (y_lo, y_hi),
            "box_n_verts": int(n_box),
        }

    blob_centre, medial, lateral = _condyle_blobs(femur_verts, slab_mm)

    if method == "notch":
        try:
            (nx, ny), gap_mm2 = _notch_in_section(
                femur_verts, fz_min + level_mm - thickness_mm / 2, thickness_mm)
            method_used = "notch"
        except ValueError:
            nx, ny, gap_mm2 = float(blob_centre[0]), float(blob_centre[1]), 0.0
            method_used = "condyle_fallback"
        return np.array([nx, ny, fz_min + level_mm]), {
            "condyle_medial": medial, "condyle_lateral": lateral, "slab_mm": float(slab_mm),
            "level_mm": float(level_mm), "notch_gap_mm2": float(gap_mm2),
            "centre_condyle_mid": blob_centre, "method": method_used,
        }

    return np.array([blob_centre[0], blob_centre[1], fz_min + level_mm]), {
        "condyle_medial": medial, "condyle_lateral": lateral, "slab_mm": float(slab_mm),
        "level_mm": float(level_mm), "notch_gap_mm2": 0.0,
        "centre_condyle_mid": blob_centre, "method": "condyle",
    }


def ankle_centre(tibia_verts, fibula_verts, search_top_mm=30.0, bin_mm=2.0):
    """Ankle joint centre from tibia + fibula meshes."""
    if len(tibia_verts) < 100 or len(fibula_verts) < 100:
        raise ValueError(f"too few verts")
    t_z_min = float(tibia_verts[:, 2].min())
    proximal = tibia_verts[tibia_verts[:, 2] < t_z_min + search_top_mm]
    if len(proximal) < 100:
        raise ValueError(f"proximal region has only {len(proximal)} tibia verts")
    bin_idx = np.floor((proximal[:, 2] - t_z_min) / bin_mm).astype(int)
    extents: dict[int, float] = {}
    for b in np.unique(bin_idx):
        xs = proximal[bin_idx == b, 0]
        if len(xs) >= 10:
            extents[int(b)] = float(xs.max() - xs.min())
    if not extents:
        raise ValueError("no bin had enough verts to measure width")
    max_ext = max(extents.values())
    top_bins = [b for b, e in extents.items() if e >= max_ext - 1.0]
    plafond_z = float(np.mean([t_z_min + (b + 0.5) * bin_mm for b in top_bins]))
    tol = bin_mm / 2.0
    tibia_at = tibia_verts[np.abs(tibia_verts[:, 2] - plafond_z) < tol]
    fibula_at = fibula_verts[np.abs(fibula_verts[:, 2] - plafond_z) < tol]
    if len(tibia_at) < 10 or len(fibula_at) < 10:
        raise ValueError(f"not enough verts at plafond_z={plafond_z:.1f}")
    median_x = float(np.median(tibia_verts[:, 0]))
    if median_x < 0:
        medial_x = float(tibia_at[:, 0].max())
        lateral_x = float(fibula_at[:, 0].min())
    else:
        medial_x = float(tibia_at[:, 0].min())
        lateral_x = float(fibula_at[:, 0].max())
    ankle_x = (medial_x + lateral_x) / 2.0
    ankle_y = float(tibia_at[:, 1].mean())
    ankle_z = plafond_z
    return np.array([ankle_x, ankle_y, ankle_z]), {
        "plafond_z": plafond_z, "medial_x": medial_x, "lateral_x": lateral_x,
    }