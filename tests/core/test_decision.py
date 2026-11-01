"""Protect the three branches of the verdict rule."""
from femuralabs.toolkit.reporting.decision import verdict


def test_verdict_three_outcomes():
    base = [0.900, 0.902, 0.898]
    # d=0.010, spread=0.002, interval [0.006, 0.014], threshold 0.005 → supported
    assert verdict(base, [0.912, 0.910, 0.908], 0.005) == "supported"
    # d=0.000, spread=0.002, interval [-0.004, 0.004], threshold 0.005 → not supported
    assert verdict(base, [0.901, 0.899, 0.900], 0.005) == "not supported"
    # d=0.010, spread=0.020, interval [-0.030, 0.050], threshold 0.005 → inconclusive
    assert verdict([0.88, 0.90, 0.92], [0.89, 0.91, 0.93], 0.005) == "inconclusive"


def test_verdict_refuses_single_run():
    """One run per variant cannot estimate spread; the function refuses."""
    import pytest
    with pytest.raises(ValueError):
        verdict([0.9], [0.95], 0.005)