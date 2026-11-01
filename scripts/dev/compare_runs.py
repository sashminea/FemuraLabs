"""Print the largest gap in val_loss between two metrics files."""

import sys
from pathlib import Path

from femuralabs.toolkit.training.train_utils import  max_abs_diff

def main() -> int:
	a, b = Path(sys.argv[1]), Path(sys.argv[2])
	diff = max_abs_diff(a, b)
	print(f"max difference in val_loss: {diff:.2e}")
	return 0

if __name__ == "__main__":
	raise SystemExit(main())

