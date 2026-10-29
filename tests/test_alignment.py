"""Tests for HKA deviation and MAD on synthetic limbs."""
from __future__ import annotations

import numpy as np
import pytest

from femuralabs.toolkit.alignment import (
    hka_deviation,
    mad,
    knee_error_to_angle_deg,
)


# Points in LPS mm. z decreases inferiorly, matching the pipeline's
# z-toward-superior convention. x = -100 is the right side of the body
# (LPS), x = +100 is the left side. The two sides are mirrored in x
# only; y is 0 throughout (a straight coronal-plane synthetic limb).

R_HIP = np.array([-100.0, 0.0,    0.0])
L_HIP = np.array([ 100.0, 0.0,    0.0])


def test_straight_limb_has_zero_hka_and_zero_mad():
    """Straight limb: HKA deviation 0 degrees, MAD 0 mm. Both sides."""
    for hip in (R_HIP, L_HIP):
        knee  = hip + np.array([0.0, 0.0, -420.0])
        ankle = hip + np.array([0.0, 0.0, -820.0])
        assert hka_deviation(hip, knee, ankle) == pytest.approx(0.0, abs=1e-9)
        assert mad(hip, knee, ankle)          == pytest.approx(0.0, abs=1e-9)


def test_bent_limb_varus_is_positive_both_sides():
    """Sprint-doc example (b): 20 mm knee lateral offset, both sides.

    Positive = varus, negative = valgus. The right leg's lateral
    direction is -x in LPS; the left leg's is +x. Both must produce the
    same positive number when the knee is 20 mm toward that side.
    """
    # Right leg: knee 20 mm lateral (more negative x).
    r_knee  = np.array([-120.0, 0.0, -420.0])
    r_ankle = R_HIP + np.array([0.0, 0.0, -820.0])
    hka_r = hka_deviation(R_HIP, r_knee, r_ankle)
    mad_r = mad(R_HIP, r_knee, r_ankle)

    # Left leg: knee 20 mm lateral (more positive x).
    l_knee  = np.array([ 120.0, 0.0, -420.0])
    l_ankle = L_HIP + np.array([0.0, 0.0, -820.0])
    hka_l = hka_deviation(L_HIP, l_knee, l_ankle)
    mad_l = mad(L_HIP, l_knee, l_ankle)

    assert hka_r == pytest.approx(5.589, abs=0.01)
    assert hka_l == pytest.approx(5.589, abs=0.01)
    assert mad_r == pytest.approx(20.0,  abs=0.01)
    assert mad_l == pytest.approx(20.0,  abs=0.01)


def test_bent_limb_valgus_flips_the_sign():
    """Same 20 mm offset, medial side: both numbers flip sign."""
    r_knee  = np.array([ -80.0, 0.0, -420.0])   # medial on right side
    r_ankle = R_HIP + np.array([0.0, 0.0, -820.0])
    assert hka_deviation(R_HIP, r_knee, r_ankle) == pytest.approx(-5.589, abs=0.01)
    assert mad(R_HIP, r_knee, r_ankle)          == pytest.approx(-20.0,  abs=0.01)


def test_mild_bend_matches_exact_arccos():
    """Sprint-doc example (c): 18 mm and 12 mm knee/ankle offsets.

    The sprint doc gives 0.74 degrees using the small-angle arctan
    approximation. The exact arccos value is ~0.736. The test asserts
    against the exact value so it documents what the code actually
    computes; both round to 0.74.
    """
    r_knee  = np.array([-118.0, 0.0, -420.0])
    r_ankle = np.array([-130.0, 0.0, -820.0])
    hka    = hka_deviation(R_HIP, r_knee, r_ankle)
    mad_mm = mad(R_HIP, r_knee, r_ankle)
    assert hka    == pytest.approx(0.736, abs=0.01)
    assert mad_mm == pytest.approx(2.632, abs=0.01)


def test_knee_error_to_angle_deg_helper():
    """2 mm of knee displacement over a 420 mm segment is ~0.273 degrees."""
    assert knee_error_to_angle_deg(2.0, 420.0) == pytest.approx(0.273, abs=0.001)