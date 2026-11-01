"""Print the geometry of a synthetic or saved volume."""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from femuralabs.toolkit.imaging.volume_info import describe, make_volume
from femuralabs.toolkit.reporting.report import write_info

LABELS = {

	"shape": "shape (z, y, x)",
	"spacing": "spacing (mm)",
	"dtype": "dtype",
	"extent_mm": "extent (mm)",

}

def build_parser() -> argparse.ArgumentParser:
	"""Describe the command line: one optional file, one optional shape, one optional spacing."""
	parser = argparse.ArgumentParser(description="Print the geometry of a volume.")
	parser.add_argument(
		"--file",
		type=Path,
		help="path to a .npy volume with axes (z, y, x); omit to build a zero volume",
	)
	parser.add_argument(
		"--shape",
		type=int,
		nargs=3,
		default=(4, 6, 6),
		help="voxel count along (z, y, x) for the zero volume; ignored with --file",	
	)
	parser.add_argument(
		"--spacing",
		type=float,
		nargs=3,
		default=(2.0, 1.0, 1.0),
		help="physical size of one voxel in mm along (z, y, x); used with either input",
	)
	parser.add_argument(
		"--out",
		type=Path,
		default=None,
		help="folder that receives info.json; omit to skip writing",
	)
	return parser

def main(argv=None) -> int:
	"""Run the tool; argv=None reads the real terminal words."""
	args = build_parser().parse_args(argv)
	if args.file is not None:
		volume = np.load(args.file)
	else:
		volume, _ = make_volume(tuple(args.shape))
	info = describe(volume, tuple(args.spacing))
	for key, label in LABELS.items():
		print(f"{label}: {info[key]}")
	if args.out is not None:
		path = write_info(info, args.out)
		print(f"wrote: {path}")
	return 0

if __name__ == "__main__":
	raise SystemExit(main())

