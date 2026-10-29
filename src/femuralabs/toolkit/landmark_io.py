"""Read landmark point lists written by 3D Slicer's Markups module."""
from __future__ import annotations

import json
from pathlib import Path


def load_landmarks(path: Path | str) -> dict[str, tuple[float, float, float]]:
    """Return {name: (x, y, z)} from a Slicer .mrk.json file.

    Slicer stores points in RAS millimetres; this function converts to LPS
    (x and y negated) so the result matches SimpleITK's world frame and
    the pipeline's Volume.origin.
    """
    data = json.loads(Path(path).read_text())
    result: dict[str, tuple[float, float, float]] = {}
    for markup in data.get("markups", []):
        for i, cp in enumerate(markup.get("controlPoints", [])):
            name = cp.get("label") or f"point_{i}"
            x, y, z = cp["position"]
            result[name] = (-x, -y, z)
    return result


def repeat_distances(
    a: dict[str, tuple[float, float, float]],
    b: dict[str, tuple[float, float, float]],
) -> dict[str, float]:
    """For each shared name, the Euclidean distance between two placements (mm)."""
    import numpy as np
    return {
        name: float(np.linalg.norm(np.array(a[name]) - np.array(b[name])))
        for name in a
        if name in b
    }