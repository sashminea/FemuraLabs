"""Write a dictionary to a JSON file, creating parent folders."""

from __future__ import annotations

import json
from pathlib import Path

def save_json(path: Path | str, data: dict, *, indent: int | None = None) -> Path:
	"""Write `data` as JSON to `path` and return the path.

	Creates parent folders. Appends a trailing newline so text editors and `cat` do not concatentate the last line with the shell prompt. `indent` is passed to `json.dumps`:`None` (default) writes compact single-line JSON, `2` writes indented human-readable JSON.
	"""

	path = Path(path)
	path.parent.mkdir(parents=True, exist_ok=True)
	path.write_text(json.dumps(data, indent=indent) + "\n")
	return path
