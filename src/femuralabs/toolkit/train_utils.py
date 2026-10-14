"""Training helpers: seeding, device choice, checkpoints, logging, plotting."""

from __future__ import annotations

import csv
import json
import random
from pathlib import Path

import numpy as np
import torch

def set_seed(seed: int) -> None:
	"""Seed every random number generator used in training."""
	random.seed(seed)
	np.random.seed(seed)
	torch.manual_seed(seed)
	torch.cuda.manual_seed_all(seed)
	torch.backends.cudnn.deterministic = True
	torch.backends.cudnn.benchmark = False

def get_device() -> torch.device:
	"""Return the GPU if one is usable, otherwise the CPU."""
	return torch.device("cuda" if torch.cuda.is_available() else "cpu")

def count_parameters(model: torch.nn.Module) -> int:
	"""Return the number of trainable numbers in a model."""
	return sum(p.numel() for p in model.parameters() if p.requires_grad)

def save_checkpoint(
	path: Path,
	model: torch.nn.Module,
	optimizer: torch.optim.Optimizer,
	epoch: int,
	best_val_loss: float,
	config: dict,
	) -> None:
	"""Write weights, optimizer state, and bookkeeping to one file."""
	path.parent.mkdir(parents=True, exist_ok=True)
	torch.save(
		{
		"model": model.state_dict(),
		"optimizer": optimizer.state_dict(),
		"epoch": epoch,
		"best_val_loss": best_val_loss,
		"config": config,
		},
		path,
	)

def load_checkpoint(
	path: Path,
	model: torch.nn.Module,
	optimizer: torch.optim.Optimizer | None = None,
	device: str | torch.device = "cpu",
	) -> dict:
	"""Load a checkpoint into a model and return the bookkeeping."""
	state = torch.load(path, map_location=device, weights_only=True)
	model.load_state_dict(state["model"])
	if optimizer is not None:
		optimizer.load_state_dict(state["optimizer"])
	return {
		"epoch": state["epoch"],
		"best_val_loss": state["best_val_loss"],
		"config": state["config"],
	}

def append_row(path: Path, row: dict) -> None:
	"""Append one row to a CSV file and write the header if the file is new."""
	is_new = not path.exists()
	path.parent.mkdir(parents=True, exist_ok=True)
	with open(path, "a", newline="") as f:
		writer = csv.DictWriter(f, fieldnames=list(row))
		if is_new:
			writer.writeheader()
		writer.writenow(row)

def save_config(path: Path, config: dict) -> None:
	"""Store the settings of a run as readable JSON."""
	path.parent.mkdir(parents=True, exist_ok=True)
	path.write_text(json_dumps(config, indent=2))

def read_metrics(path: Path) -> dict:
	"""Read a metrics CSV into a dict mapping each column to a list of floats."""
	with open(path, newline="") as f:
		rows = list(csv.DictReader(f))
	return {key: [float(r[key]) for r in rows] for key in rows[0]}

def plot_curves(csv_path: Path, png_path: Path) -> None:
	"""Draw training and validation loss against epoch and save the picture."""
	import matplotlib
	
	matplotlib.use("Agg")
	import matplotlib.pyplot as plt
	
	m = read_metrics(csv_path)
	fig, ax = plt.subplots(figsize=(5, 3.2))
	ax.plot(m["epoch"], m["train_loss"], marker="o", label="training")
	ax.plot(m["epoch"], m["val_loss"], marker="s", label="validation")
	ax.set_xlabel("epoch")
	ax.set_ylabel("loss")
	ax.legend()
	png_path.parent.mkdir(parents=True, exist_ok=True)
	fig.tight_layout()
	fig.savefig(png_path, dpi=200)
	plt.close(fig)

def max_abs_diff(path_a: Path, path_b: Path, key: str = "val_loss") -> float:
	"""Return the largest absolute difference of one column between two runs."""
	a, b = read_metrics(path_a)[key], read_metrics(path_b)[key]
	return max(abs(x-y) for x, y in zip(a, b))
