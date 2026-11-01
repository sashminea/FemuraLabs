"""Print the shape and spacing of a synthetic volume."""

import numpy as np
from femuralabs.toolkit.imaging.volume_info import make_volume


if __name__ == "__main__":
	volume, spacing = make_volume()
	print("shape (z, y, x):", volume.shape)
	print("spacing (mm):", spacing)
	print("dtype:", volume.dtype)
