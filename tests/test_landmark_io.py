"""Test landmark loading and repeat-distance measurement."""
import json
from pathlib import Path

import pytest

from femuralabs.toolkit.landmark_io import load_landmarks, repeat_distances


def test_ras_to_lps_conversion(tmp_path):
    path = tmp_path / "landmarks.mrk.json"
    path.write_text(json.dumps({
        "markups": [{
            "controlPoints": [
                {"label": "femoral_head_R", "position": [100.0, 200.0, 50.0]},
                {"label": "knee_centre_R", "position": [-10.0, 5.0, -100.0]},
            ]
        }]
    }))
    result = load_landmarks(path)
    assert result["femoral_head_R"] == (-100.0, -200.0, 50.0)
    assert result["knee_centre_R"] == (10.0, -5.0, -100.0)

def test_lps_file_passes_through_unchanged(tmp_path):
    path = tmp_path / "landmarks.mrk.json"
    path.write_text(json.dumps({
        "markups": [{
            "coordinateSystem": "LPS",
            "controlPoints": [
                {"label": "femoral_head_R", "position": [-94.2, -156.3, 1100.0]},
            ]
        }]
    }))
    assert load_landmarks(path)["femoral_head_R"] == (-94.2, -156.3, 1100.0)

def test_unnamed_point_falls_back_to_index(tmp_path):
    path = tmp_path / "landmarks.mrk.json"
    path.write_text(json.dumps({
        "markups": [{"controlPoints": [{"position": [1.0, 2.0, 3.0]}]}]
    }))
    assert load_landmarks(path)["point_0"] == (-1.0, -2.0, 3.0)


def test_repeat_distances():
    a = {"femoral_head_R": (0.0, 0.0, 0.0), "knee_centre_R": (10.0, 0.0, 0.0)}
    b = {"femoral_head_R": (3.0, 4.0, 0.0), "knee_centre_R": (10.0, 0.0, 0.0)}
    d = repeat_distances(a, b)
    assert d["femoral_head_R"] == pytest.approx(5.0)
    assert d["knee_centre_R"] == pytest.approx(0.0)