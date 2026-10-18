import numpy as np

def make_volume(shape=(4, 6, 6), spacing=(2.0, 1.0, 1.0)):
	volume = np.zeros(shape, dtype=np.float32)
	return volume, spacing

volume, spacing = make_volume()
print("shape (z, y,x):", volume.shape)
print("spacing (mm):", spacing)
print("dtype:", volume.dtype)
