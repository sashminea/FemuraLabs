"""Tests for train_utils: seeding and checkpoint round trip."""

import torch

from femuralabs.toolkit.training.model import SmallCNN
from femuralabs.toolkit.training.train_utils import load_checkpoint, save_checkpoint, set_seed

def test_same_seed_same_number():
	set_seed(3)
	a = torch.rand(3)
	set_seed(3)
	b = torch.rand(3)
	assert torch.equal(a, b)

def test_checkpoint_round_trip(tmp_path):
	
	model = SmallCNN()
	opt = torch.optim.SGD(model.parameters(), lr=0.1)
	save_checkpoint(tmp_path / "c.pt", model, opt, 2, 0.5, {"seed": 1})

	other = SmallCNN()
	info = load_checkpoint(tmp_path / "c.pt", other)

	assert info["epoch"] == 2
	assert info["best_val_loss"] == 0.5
	assert info["config"] == {"seed": 1}
	
	for p, q in zip(model.parameters(), other.parameters()):
		assert torch.equal(p, q)


