"""Protect write_info: it creates the folder, writes info.json, returns the path."""

import json

from femuralabs.toolkit.report import write_info
from femuralabs.toolkit.volume_info import describe, make_volume

def test_write_info_creates_folder_and_file(tmp_path):
	"""Two levels deep, neither exists yet: proves parents=True and exist_ok=True."""

	info = describe(*make_volume())
	target = tmp_path / "a" / "output"
	path = write_info(info, target)

	assert path == target / "info.json"
	assert path.exists()

	body = json.loads(path.read_text())
	assert body["extent_mm"] == [8.0, 6.0, 6.0]
	assert path.read_text().endswith("\n")

def test_write_info_is_idempotent(tmp_path):
	"""Two calls on a same folder overwrite cleanly; the second does not raise."""

	info = describe(*make_volume())
	first = write_info(info, tmp_path)
	second = write_info(info, tmp_path)
	assert first == second
	assert first.exists()

	

