"""Array helpers: normalisation, windowing and a slow reference convolution."""

from __future__ import annotations

import numpy as np

def zscore_batch(batch: np.ndarray, eps: float=1e-8) -> np.ndarray:
	"""Normalise each volume of a (B, Z, Y, X) batch to mean 0, std 1."""

	b = batch.astype(np.float32)
	mean = b.mean(axis=(1, 2, 3), keepdims=True)
	std = b.std(axis=(1, 2, 3), keepdims=True)
	return (b - mean) / (std + eps)

