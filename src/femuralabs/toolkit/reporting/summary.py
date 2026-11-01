"""Summarize a NumPy array stored in a .npy file."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import numpy as np

@dataclass(frozen=True)
class ArraySummary:
	shape: tuple
	dtype: str
	minimum: float
	maximum: float
	mean: float

def summarise(array: np.ndarray) -> ArraySummary:
	"""Return shape, dtype, min, max and mean of an array in memory."""
	return ArraySummary(
		tuple(array.shape),
		str(array.dtype),
		float(array.min()),
		float(array.max()),
		float(array.mean()),
		)

def load_and_summarise(path: Path) -> ArraySummary:
	"""Load a .npy file from path and summarise it."""
	if path.suffix != ".npy":
		raise ValueError(f"Expected a .npy file, got: {path.name}")
	if not path.is_file():
		raise FileNotFoundError(f"No such file: {path}")

	return summarise(np.load(path))

def build_parser() -> argparse.ArgumentParser:
	"""Describe the command line: one required argument, the file path."""
	parser = argparse.ArgumentParser(
		description="Print a summary of a .npy array."
		)
	parser.add_argument("path", type=Path, help="path to a .npy file")
	return parser

def main(argv=None) -> int:
	"""Run the tool; argv=None means the real terminal words."""
	args = build_parser().parse_args(argv)
	s = load_and_summarise(args.path)
	print(
		f"shape: {s.shape}\n"
		f"dtype: {s.dtype}\n"
		f"min: {s.minimum:.2f}\n"
		f"max: {s.maximum:.2f}\n"
		f"mean: {s.mean:.2f}\n"
	)
	return 0

if __name__ == "__main__":
	raise SystemExit(main())


