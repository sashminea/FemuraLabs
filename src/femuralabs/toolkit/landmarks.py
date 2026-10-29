"""Landmark extraction from bone meshes."""
from __future__ import annotations

import numpy as np


def fit_sphere(points: np.ndarray) -> tuple[np.ndarray, float, float]:
    """Least-squares sphere fit.

    Solves x^2 + y^2 + z^2 = 2ax + 2by + 2cz + d for (a, b, c, d), which
    is linear in the four unknowns. Returns (centre, radius, rms_residual).
    The residual is the root-mean-square deviation of point-to-surface
    distance, in the units of `points`.
    """
    if len(points) < 4:
        raise ValueError(f"Need at least 4 points, got {len(points)}")
    A = np.column_stack([
        2.0 * points[:, 0],
        2.0 * points[:, 1],
        2.0 * points[:, 2],
        np.ones(len(points)),
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
    verts: np.ndarray,
    n_iter: int = 3,
    medial_window_mm: float = 20.0,
) -> tuple[np.ndarray, float, float]:
    """Estimate the femoral head centre from a femur mesh.

    The head is the medial-most spherical feature of the proximal femur.
    Two constraints make the fit land on the head rather than averaging
    the head with the trochanter:

    - **z cut**: keep only the superior 25 percent of the mesh. Both the
      head and the trochanter are superior, so this is necessary but not
      sufficient.
    - **medial window**: keep only vertices within ``medial_window_mm`` of
      the medial-most x. The head is the medial-most feature, so this
      window captures its medial hemisphere, which is enough to constrain
      a sphere fit; larger windows start to include the greater trochanter,
      which is not spherical and pulls the centre laterally.

    On case01, a window of 20 mm gives fit radii 18.3 (right) and 20.4
    (left) mm and centre errors 3.81 and 4.82 mm versus hand placement.
    A window of 30+ mm gives radii 31-33 mm (a head-plus-trochanter blend)
    and errors over 20 mm.
    """
    z = verts[:, 2]
    z_lo, z_hi = float(z.min()), float(z.max())
    cut = z_lo + 0.75 * (z_hi - z_lo)
    proximal = verts[z > cut]
    if len(proximal) < 100:
        raise ValueError(
            f"Proximal region has only {len(proximal)} vertices; "
            "the mesh may be truncated"
        )

    median_x = float(np.median(verts[:, 0]))
    if median_x < 0:
        # Patient's right side: medial is closer to 0, i.e. larger x
        medial_x = float(proximal[:, 0].max())
        region = proximal[proximal[:, 0] > medial_x - medial_window_mm]
    else:
        # Patient's left side: medial is closer to 0, i.e. smaller x
        medial_x = float(proximal[:, 0].min())
        region = proximal[proximal[:, 0] < medial_x + medial_window_mm]

    if len(region) < 50:
        raise ValueError(
            f"Medial window contains only {len(region)} vertices; "
            "medial_window_mm may be too tight for this mesh"
        )

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

def knee_centre(
    femur_verts: np.ndarray,
    tibia_verts: np.ndarray,
    slab_mm: float = 5.0,
) -> np.ndarray:
    """Knee joint centre from the femur and tibia meshes.

    Take a thin slab at the distal extreme of the femur (the condyles)
    and one at the proximal extreme of the tibia (the plateau). Both
    centroids sit at the joint line, central in x-y. Their midpoint
    approximates the knee joint centre.

    In LPS, superior is +z. The distal femur is therefore at the minimum
    z of the femur mesh; the proximal tibia is at the maximum z of the
    tibia mesh.
    """
    fz_min = float(femur_verts[:, 2].min())
    femur_slab = femur_verts[femur_verts[:, 2] < fz_min + slab_mm]

    tz_max = float(tibia_verts[:, 2].max())
    tibia_slab = tibia_verts[tibia_verts[:, 2] > tz_max - slab_mm]

    if len(femur_slab) < 20 or len(tibia_slab) < 20:
        raise ValueError(
            f"Slab too small: femur {len(femur_slab)}, tibia {len(tibia_slab)}"
        )
    return (femur_slab.mean(axis=0) + tibia_slab.mean(axis=0)) / 2.0


def ankle_centre(
    tibia_verts: np.ndarray,
    fibula_verts: np.ndarray,
    search_top_mm: float = 30.0,
    bin_mm: float = 2.0,
) -> tuple[np.ndarray, dict]:
    """Ankle joint centre from tibia + fibula meshes.

    The very bottom of the tibia is the tip of the medial malleolus, not
    the joint surface. The joint surface is the plafond, the flat bottom
    of the shinbone that sits on the talus. Finding it: within the bottom
    ``search_top_mm`` of the tibia, the plafond is where the cross-section
    is widest. On case01 this is ~14 mm above the malleolar tip.

    At the plafond level, take the medial edge of the tibia (medial
    malleolus) and the lateral edge of the fibula (lateral malleolus). The
    ankle centre is their midpoint — this is rule (a) in
    docs/conventions.md.

    Returns (centre, intermediates) so a failing test can show which part
    of the rule went wrong.
    """
    if len(tibia_verts) < 100 or len(fibula_verts) < 100:
        raise ValueError(
            f"too few verts: tibia {len(tibia_verts)}, fibula {len(fibula_verts)}"
        )

    # 1. Plafond z: widest cross-section in the bottom search_top_mm.
    t_z_min = float(tibia_verts[:, 2].min())
    proximal = tibia_verts[tibia_verts[:, 2] < t_z_min + search_top_mm]
    if len(proximal) < 100:
        raise ValueError(
            f"proximal region has only {len(proximal)} tibia verts; "
            f"search_top_mm={search_top_mm} too tight"
        )
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

    # 2. Verts at the plafond level (within half a bin in z).
    tol = bin_mm / 2.0
    tibia_at = tibia_verts[np.abs(tibia_verts[:, 2] - plafond_z) < tol]
    fibula_at = fibula_verts[np.abs(fibula_verts[:, 2] - plafond_z) < tol]
    if len(tibia_at) < 10 or len(fibula_at) < 10:
        raise ValueError(
            f"not enough verts at plafond_z={plafond_z:.1f}: "
            f"tibia {len(tibia_at)}, fibula {len(fibula_at)}"
        )

    # 3. Medial/lateral edges. Sign convention: in LPS, patient's right
    #    side is negative world x, so medial (toward midline = toward 0)
    #    is the larger x on R and the smaller x on L.
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

    return (
        np.array([ankle_x, ankle_y, ankle_z]),
        {
            "plafond_z": plafond_z,
            "medial_x": medial_x,
            "lateral_x": lateral_x,
        },
    )