"""A small CNN for 28x28 grayscale images with 10 classes."""

from __future__ import annotations

import torch
from torch import nn

class SmallCNN(nn.Module):
	"""Two convolution blocks and linear layer for 28x28 images."""

	def __init__(self, num_classes: int = 10) -> None:
		super().__init__()
		self.features = nn.Sequential(
			nn.Conv2d(1, 8, kernel_size=3, padding=1), # 1x28x28 -> 8x28x28
			nn.ReLU(),
			nn.MaxPool2d(2), # 8x28x28 -> 8x14x14
			nn.Conv2d(8, 16, kernel_size=3, padding=1), # 8x14x14 -> 16x14x14
			nn.ReLU(),
			nn.MaxPool2d(2), # 16x14x14 -> 16x7x7
		)
		self.classifier = nn.Linear(16 * 7 * 7, num_classes) # 784 -> 10

	def forward(self, x:torch.Tensor) -> torch.Tensor:
		x = self.features(x)
		x = torch.flatten(x, start_dim=1)
		return self.classifier(x)


