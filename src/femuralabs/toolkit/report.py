"""Write a describe() dictionary to disk as JSON."""

from __future__ import annotations

import json
from pathlib import Path

from femuralabs.toolkit.io import save_json

def write_info(info: dict, out_dir: Path | str) -> Path:
	"""Write `info` to `out_dir/info.json` and return the path it wrote.

	The caller supplies the folder; there is no default. A hidden default folder would be a global choice that a container and a host run could disagree about. `parents=True` creates missing parents; `exist_ok=True` is silent when the folder exists. The return value lets the caller print, test, or chain - a printed line cannot.
	"""

	folder = Path(out_dir)
	folder.mkdir(parents=True, exist_ok=True)
	path = folder / "info.json"
	path.write_text(json.dumps(info) + "\n")
	
	return path

def write_info(info: dict, out_dir: Path | str) -> Path:
	"""Write `info` to `out_dir/info.json` and return the path it wrote.

	The folder is a required parameter with no default: a hidden default folder would be one that a host run and a container run could silently disagree about. Uses `io.save_json` for the write, so the parent-folder creation and the trailing-newline policy are defined in one place.
	"""

	return save_json(Path(out_dir) / "info.json", info)

