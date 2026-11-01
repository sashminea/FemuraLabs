"""Build a synthetic volume and describe its geometry."""

from __future__ import annotations

import numpy as np

def make_volume(
	shape: tuple[int, int, int] = (4, 6, 6),
	spacing: tuple[float, float, float] = (2.0, 1.0, 1.0),
	) -> tuple[np.ndarray, tuple[float, float, float]]:
	"""Return a zero volume with axes (z, y, x) and its spacing in mm."""

	return np.zeros(shape, dtype=np.float32), tuple(spacing)

def describe(volume: np.ndarray, spacing) -> dict:
	"""Return shape, spacing, dtype and physical extent (mm) of a volume."""
	extent = tuple(round(n*s, 1) for n, s in zip(volume.shape, spacing))
	return {
		"shape": tuple(volume.shape),
		"spacing": tuple(spacing),
		"dtype": str(volume.dtype),
		"extent_mm": extent,
	}
