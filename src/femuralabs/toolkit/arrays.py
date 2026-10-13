"""Array helpers: normalisation, windowing and a slow reference convolution."""

from __future__ import annotations

import numpy as np

def zscore_batch(batch: np.ndarray, eps: float=1e-8) -> np.ndarray:
	"""Normalise each volume of a (B, Z, Y, X) batch to mean 0, std 1."""

	b = batch.astype(np.float32)
	mean = b.mean(axis=(1, 2, 3), keepdims=True)
	std = b.std(axis=(1, 2, 3), keepdims=True)
	return (b - mean) / (std + eps)


def window_to_uint8(hu: np.ndarray, level: float, width: float) -> np.ndarray:
	"""Map HU values to 0-255 with a linear window; for display only."""

	lower = level - width / 2.0
	d = 255.0 * (hu.astype(np.float32) - lower) / width
	return np.clip(d, 0, 255).astype(np.uint8)

def conv2d(
	image: np.ndarray,
	kernel: np.ndarray,
	stride: int = 1,
	pad: int = 0,
	) -> np.ndarray:
	"""Slide a square kernel over a square image (no kernel flip)."""
	img = np.pad(image.astype(float), pad)
	k = kernel.shape[0]
	n = (img.shape[0] - k) // stride + 1
	out = np.zeros((n, n))
	for i in range(n):
		for j in range(n):
			patch = img[i * stride : i * stride + k, j * stride : j * stride + k]
			out[i, j] = (patch * kernel).sum()
	return out
