"""HKA deviation and mechanical axis deviation (MAD) from three points.

HKA deviation and MAD are the two scalar measures of lower-limb
alignment derived from the hip, knee, and ankle centres. Both are used
in D11-D17; this module implements them in isolation so the geometry
is provable against synthetic limbs (D10 pass test) before it is
applied to real landmarks.

Sign convention: positive = varus (knee lateral of the H-A line, distal
segment tilted toward body midline), negative = valgus (knee medial).
"Lateral" depends on which side of the body the leg is: for a right leg
(hip.x < 0 in LPS), lateral = -x; for a left leg (hip.x > 0), lateral
= +x. The code detects side from hip.x sign so the returned number
carries the same anatomical meaning on both sides.
"""
from __future__ import annotations

import numpy as np


def _leg_side(hip: np.ndarray) -> int:
    """Return -1 for right leg (hip.x < 0), +1 for left leg (hip.x > 0)."""
    if hip[0] < 0:
        return -1
    if hip[0] > 0:
        return 1
    raise ValueError(
        f"hip at midline (x=0); cannot determine left/right from {hip}"
    )


def _signed_lateral_mm(hip, knee, ankle) -> float:
    """Signed lateral distance of the knee from the H-A line, in mm.

    Positive: knee on the lateral side of the hip-ankle line (varus).
    Negative: knee on the medial side (valgus).
    Zero: knee exactly on the line (straight).
    """
    hip = np.asarray(hip, dtype=float)
    knee = np.asarray(knee, dtype=float)
    ankle = np.asarray(ankle, dtype=float)
    ha = ankle - hip
    ha_len = float(np.linalg.norm(ha))
    if ha_len == 0.0:
        raise ValueError("hip and ankle are the same point")
    ha_unit = ha / ha_len
    hk = knee - hip
    perp = hk - np.dot(hk, ha_unit) * ha_unit
    side = _leg_side(hip)
    lateral_axis = np.array([float(side), 0.0, 0.0])
    return float(np.dot(perp, lateral_axis))


def _sign(x: float) -> float:
    return 1.0 if x > 0 else -1.0 if x < 0 else 0.0


def hka_deviation(hip, knee, ankle) -> float:
    """Signed HKA deviation in degrees; positive = varus, negative = valgus.

    The angle between the femoral mechanical axis (H->K) and the tibial
    mechanical axis (K->A). Zero for a straight limb.
    """
    hip = np.asarray(hip, dtype=float)
    knee = np.asarray(knee, dtype=float)
    ankle = np.asarray(ankle, dtype=float)
    hk = knee - hip
    ka = ankle - knee
    hk_len = float(np.linalg.norm(hk))
    ka_len = float(np.linalg.norm(ka))
    if hk_len == 0.0 or ka_len == 0.0:
        raise ValueError(
            f"zero-length mechanical-axis segment: |HK|={hk_len}, |KA|={ka_len}"
        )
    cos_angle = float(np.clip(np.dot(hk, ka) / (hk_len * ka_len), -1.0, 1.0))
    angle_deg = float(np.degrees(np.arccos(cos_angle)))
    return _sign(_signed_lateral_mm(hip, knee, ankle)) * angle_deg


def mad(hip, knee, ankle) -> float:
    """Signed MAD in millimetres; positive = varus, negative = valgus.

    Perpendicular distance of the knee centre from the hip-ankle line.
    """
    hip = np.asarray(hip, dtype=float)
    knee = np.asarray(knee, dtype=float)
    ankle = np.asarray(ankle, dtype=float)
    ha = ankle - hip
    hk = knee - hip
    ha_len = float(np.linalg.norm(ha))
    if ha_len == 0.0:
        raise ValueError("hip and ankle are the same point")
    distance_mm = float(np.linalg.norm(np.cross(ha, hk)) / ha_len)
    return _sign(_signed_lateral_mm(hip, knee, ankle)) * distance_mm


def knee_error_to_angle_deg(error_mm: float, segment_length_mm: float) -> float:
    """Approximate angular error (degrees) from a knee-centre displacement.

    If the knee centre is off by ``error_mm`` and the segment from it to
    a neighbouring joint has length ``segment_length_mm``, that segment's
    direction is off by roughly ``arctan(error_mm / segment_length_mm)``
    degrees. Used to decide whether an observed HKA deviation is real
    signal or just knee-centre placement noise.
    """
    if segment_length_mm <= 0:
        raise ValueError(
            f"segment_length_mm must be positive, got {segment_length_mm}"
        )
    return float(np.degrees(np.arctan(error_mm / segment_length_mm)))