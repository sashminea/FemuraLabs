"""Tests for agreement statistics."""
import pytest
from femuralabs.toolkit.geometry.stats import mean_std, confidence_interval, bland_altman


def test_mean_std():
    data = [0.8, -0.4, 1.2]
    mean, std = mean_std(data)
    assert mean == pytest.approx(0.5333, abs=1e-4)
    assert std == pytest.approx(0.8327, abs=1e-4)


def test_confidence_interval():
    # Sprint doc example (a): n=10, mean 0.94, SD 0.03 -> SE=0.00949, margin=0.02146
    data = [0.94] * 9 + [0.94 + 0.03 * 3.162]  # Constructed to give SD ~0.03
    # Instead of constructing, let's use the exact sprint doc math:
    # If SE = 0.03 / sqrt(10) = 0.0094868, t=2.262, margin = 0.02146
    # CI = (0.9185, 0.9615)
    data_10 = [0.94] * 10
    # We can't test SD with all identical values, so let's use the (b) example:
    # Differences 0.8, -0.4, 1.2. Mean=0.533, SD=0.8327. SE=0.4807. t(2)=4.303. margin=2.069.
    # CI = (-1.54, 2.60)
    data_b = [0.8, -0.4, 1.2]
    lo, hi = confidence_interval(data_b)
    assert lo == pytest.approx(-1.536, abs=1e-2)
    assert hi == pytest.approx(2.602, abs=1e-2)


def test_bland_altman():
    # Sprint doc example (b): Differences 0.8, -0.4, 1.2
    # Bias = 0.533. SD = 0.8327. Limits = 0.533 ± 1.96*(0.8327) = (-1.10, 2.17)
    data = [0.8, -0.4, 1.2]
    bias, loa_lo, loa_hi = bland_altman(data)
    assert bias == pytest.approx(0.533, abs=1e-3)
    assert loa_lo == pytest.approx(-1.10, abs=1e-2)
    assert loa_hi == pytest.approx(2.17, abs=1e-2)