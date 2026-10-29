"""Tests for sphere fit and femoral head detection."""
from pathlib import Path

import numpy as np
import pytest

from femuralabs.toolkit.io_volume import load_volume
from femuralabs.toolkit.landmark_io import load_landmarks
from femuralabs.toolkit.landmarks import fit_sphere, femoral_head_centre
from femuralabs.toolkit.masks import extract_masks
from femuralabs.toolkit.mesh import mask_to_mesh


COMBINED = Path("data/raw/case01/combined_seg.nii")
LMK = Path("data/ref/landmarks_case01.mrk.json")


def test_sphere_fit_recovers_synthetic_centre():
    """Noise-free synthetic sphere must recover centre to 1e-6."""
    rng = np.random.default_rng(0)
    true_centre = np.array([10.0, -20.0, 30.0])
    true_radius = 25.0
    theta = rng.uniform(0, 2 * np.pi, 200)
    phi = np.arccos(rng.uniform(-1, 1, 200))
    points = true_centre + true_radius * np.column_stack([
        np.sin(phi) * np.cos(theta),
        np.sin(phi) * np.sin(theta),
        np.cos(phi),
    ])
    centre, radius, rms = fit_sphere(points)
    assert np.allclose(centre, true_centre, atol=1e-6)
    assert radius == pytest.approx(true_radius, rel=1e-6)
    assert rms < 1e-6


def test_sphere_fit_with_noise():
    """1 mm Gaussian noise on a 25 mm sphere: centre error under 0.5 mm."""
    rng = np.random.default_rng(1)
    true_centre = np.array([10.0, -20.0, 30.0])
    true_radius = 25.0
    theta = rng.uniform(0, 2 * np.pi, 1000)
    phi = np.arccos(rng.uniform(-1, 1, 1000))
    points = true_centre + true_radius * np.column_stack([
        np.sin(phi) * np.cos(theta),
        np.sin(phi) * np.sin(theta),
        np.cos(phi),
    ])
    points += rng.normal(0.0, 1.0, size=points.shape)
    centre, radius, rms = fit_sphere(points)
    assert np.linalg.norm(centre - true_centre) < 0.5
    assert rms < 1.5


@pytest.fixture(scope="module")
def real_case():
    if not COMBINED.exists() or not LMK.exists():
        pytest.skip("real case or hand landmarks missing")
    volume = load_volume(COMBINED)
    masks = extract_masks(volume)
    hand = load_landmarks(LMK)
    return volume, masks, hand


def test_femoral_head_right_agrees_with_hand_placement(real_case):
    """Sphere-fit head centre has a plausible radius and is within 10 mm."""
    volume, masks, hand = real_case
    verts, _ = mask_to_mesh(
        masks["femur_R"].mask, volume.spacing, volume.origin, volume.direction,
    )
    centre, radius, rms = femoral_head_centre(verts)
    # Radius check first: it is the more diagnostic signal
    assert 17.0 < radius < 25.0, (
        f"implausible head radius {radius:.1f} mm — the fit is not the head"
    )
    reference = np.array(hand["femoral_head_R"])
    error_mm = float(np.linalg.norm(centre - reference))
    assert error_mm < 10.0, (
        f"head centre error {error_mm:.2f} mm; "
        f"fit centre {centre.round(1)} vs hand {reference.round(1)}; "
        f"radius {radius:.1f} mm, rms {rms:.2f} mm"
    )


def test_femoral_head_left_agrees_with_hand_placement(real_case):
    volume, masks, hand = real_case
    verts, _ = mask_to_mesh(
        masks["femur_L"].mask, volume.spacing, volume.origin, volume.direction,
    )
    centre, radius, rms = femoral_head_centre(verts)
    assert 17.0 < radius < 25.0, (
        f"implausible head radius {radius:.1f} mm"
    )
    reference = np.array(hand["femoral_head_L"])
    error_mm = float(np.linalg.norm(centre - reference))
    assert error_mm < 10.0, (
        f"head centre error {error_mm:.2f} mm; "
        f"fit centre {centre.round(1)} vs hand {reference.round(1)}; "
        f"radius {radius:.1f} mm, rms {rms:.2f} mm"
    )