"""Read landmark point lists written by 3D Slicer's Markups module."""
from __future__ import annotations

import json
from pathlib import Path


def load_landmarks(path: Path | str) -> dict[str, tuple[float, float, float]]:
    """Return {name: (x, y, z)} from a Slicer .mrk.json file in LPS.

    Slicer writes ``coordinateSystem`` for each markup. If it says RAS,
    negate x and y to get LPS (the pipeline's frame). If it says LPS (the
    default in Slicer 5.x), the values are already in LPS — do not negate.
    An unset field is treated as LPS, matching Slicer's own default.
    """
    data = json.loads(Path(path).read_text())
    result: dict[str, tuple[float, float, float]] = {}
    for markup in data.get("markups", []):
        cs = markup.get("coordinateSystem", "LPS")
        for i, cp in enumerate(markup.get("controlPoints", [])):
            name = cp.get("label") or f"point_{i}"
            x, y, z = cp["position"]
            result[name] = (-x, -y, z) if cs == "RAS" else (x, y, z)
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