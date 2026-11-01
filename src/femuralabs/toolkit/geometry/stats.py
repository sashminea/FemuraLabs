"""Statistical measures for method agreement."""
from __future__ import annotations

import math
import numpy as np
from scipy import stats as scipy_stats


def mean_std(data: list[float]) -> tuple[float, float]:
    """Return the mean and sample standard deviation (n-1 divisor)."""
    if len(data) < 2:
        raise ValueError("Need at least 2 values to compute standard deviation")
    arr = np.array(data, dtype=float)
    return float(np.mean(arr)), float(np.std(arr, ddof=1))


def confidence_interval(data: list[float], confidence: float = 0.95) -> tuple[float, float]:
    """Return the lower and upper bounds of the confidence interval for the mean."""
    n = len(data)
    if n < 2:
        raise ValueError("Need at least 2 values to compute CI")
    
    mean, std = mean_std(data)
    se = std / math.sqrt(n)
    
    # Two-tailed t-value for the given confidence level
    alpha = 1.0 - confidence
    t_val = scipy_stats.t.ppf(1 - alpha / 2, df=n - 1)
    
    margin = t_val * se
    return float(mean - margin), float(mean + margin)


def bland_altman(diffs: list[float]) -> tuple[float, float, float]:
    """Return (bias, lower_limit, upper_limit) for a set of differences.
    
    Bias is the mean difference. Limits of agreement are bias ± 1.96 * SD.
    """
    mean, std = mean_std(diffs)
    loa_lower = mean - 1.96 * std
    loa_upper = mean + 1.96 * std
    return float(mean), float(loa_lower), float(loa_upper)