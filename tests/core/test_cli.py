"""Protect the CLI's subprocess invocation."""
import os
import subprocess
import sys

ENV = {**os.environ, "PYTHONPATH": "src"}


def test_cli_prints_geometry():
    """`python -m femuralabs.toolkit.cli` exits 0 and prints the four expected lines."""
    run = subprocess.run(
        [sys.executable, "-m", "femuralabs.toolkit.cli"],
        capture_output=True,
        text=True,
        check=True,
        env=ENV,
    )
    assert "shape (z, y, x): (4, 6, 6)" in run.stdout
    assert "spacing (mm): (2.0, 1.0, 1.0)" in run.stdout
    assert "dtype: float32" in run.stdout
    assert "extent (mm): (8.0, 6.0, 6.0)" in run.stdout


def test_cli_accepts_shape_and_spacing_flags():
    """`--shape 3 5 5 --spacing 1.5 1.5 1.5` produces the extent computed by hand."""
    run = subprocess.run(
        [
            sys.executable,
            "-m",
            "femuralabs.toolkit.cli",
            "--shape", "3", "5", "5",
            "--spacing", "1.5", "1.5", "1.5",
        ],
        capture_output=True,
        text=True,
        check=True,
        env=ENV,
    )
    assert "extent (mm): (4.5, 7.5, 7.5)" in run.stdout