import numpy as np

from femuralabs.toolkit.arrays import zscore_batch

def test_zscore_removes_brightness_and_scale():
	v = np.arange(24, dtype=float).reshape(2, 3, 4)
	z = zscore_batch(np.stack([v, 2 * v + 5]))
	assert np.allclose(z[0], z[1], atol=1e-4)
	assert np.allclose(z.mean(axis=(1, 2, 3)), 0, atol=1e-5)
	assert np.allclose(z.std(axis=(1, 2, 3)), 1, atol=1e-5)

