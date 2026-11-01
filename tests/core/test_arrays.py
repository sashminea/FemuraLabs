import numpy as np

from femuralabs.toolkit.imaging.arrays import zscore_batch
from femuralabs.toolkit.imaging.arrays import window_to_uint8
from femuralabs.toolkit.imaging.arrays import conv2d

def test_zscore_removes_brightness_and_scale():
	v = np.arange(24, dtype=float).reshape(2, 3, 4)
	z = zscore_batch(np.stack([v, 2 * v + 5]))
	assert np.allclose(z[0], z[1], atol=1e-4)
	assert np.allclose(z.mean(axis=(1, 2, 3)), 0, atol=1e-5)
	assert np.allclose(z.std(axis=(1, 2, 3)), 1, atol=1e-5)


def test_window_single_value():
	#  HU 200, L 400, W 1500 -> 93.5 on paper, 93 after uint8 truncation
	out = window_to_uint8(np.array([200.0]), 400, 1500)
	assert out[0] == 93
	assert out.dtype == np.uint8

def test_window_clips_at_edges():
	out = window_to_uint8(np.array([-1000.0, 1000.0]), 400, 1500)
	assert out[0] == 0
	assert out[1] == 229


SOBEL = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]])

IMG = np.array(
	[
		[1, 2, 0, 1, 3],
		[3, 1, 2, 0, 1],
		[0, 2, 1, 3, 2],
		[1, 0, 2, 1, 0],
		[2, 1, 0, 2, 1],
	])

def test_conv_matches_hand_result():
	hand = np.array(
		[
			[-2, -2, 2],
			[2, 2, -1],
			[1, 4, -2],
		]
		)
	assert np.allclose(conv2d(IMG, SOBEL), hand)

def test_conv_output_size_formula():
	out = conv2d(np.zeros((128, 128)), np.ones((3, 3)), stride=2, pad=1)
	assert out.shape == (64, 64)
