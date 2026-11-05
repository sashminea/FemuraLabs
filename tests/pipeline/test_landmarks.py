"""Tests for sphere fit, femoral head detection, and joint centres."""
from pathlib import Path

import numpy as np
import pytest

from femuralabs.toolkit.fileio.volume import load_volume
from femuralabs.toolkit.fileio.landmark import load_landmarks
from femuralabs.toolkit.geometry.landmarks import (
    fit_sphere, femoral_head_centre, ankle_centre, knee_centre
)
from femuralabs.toolkit.imaging.masks import extract_masks
from femuralabs.toolkit.imaging.mesh import mask_to_mesh

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


def test_ankle_centre_right_agrees_with_hand_placement(real_case):
    """Ankle centre from malleolar midpoint; error under 6 mm.
    
    Diagnostic boundary: the y-delta on this side is -3.0 mm, at the
    edge of the "revisit skipping talus" decision. If a future change
    pushes dy past 3 mm, the tibia-centroid-as-talar-proxy assumption
    in ankle_centre is the part to check.
    """
    volume, masks, hand = real_case
    tv, _ = mask_to_mesh(
        masks["tibia_R"].mask, volume.spacing, volume.origin, volume.direction,
    )
    fv, _ = mask_to_mesh(
        masks["fibula_R"].mask, volume.spacing, volume.origin, volume.direction,
    )
    centre, info = ankle_centre(tv, fv)

    tibia_z_min = float(tv[:, 2].min())
    assert info["plafond_z"] > tibia_z_min + 10.0, (
        f"plafond_z={info['plafond_z']:.1f} is too close to tibia bottom "
        f"{tibia_z_min:.1f}; picked the malleolar tip, not the plafond"
    )
    assert info["medial_x"] > info["lateral_x"], (
        f"on the right side medial should exceed lateral; "
        f"got medial_x={info['medial_x']:.1f}, "
        f"lateral_x={info['lateral_x']:.1f}"
    )
    reference = np.array(hand["ankle_centre_R"])
    error_mm = float(np.linalg.norm(centre - reference))
    assert error_mm < 6.0, (
        f"ankle error {error_mm:.2f} mm; auto {centre.round(1)} vs "
        f"hand {reference.round(1)}; info={info}"
    )


def test_ankle_centre_left_agrees_with_hand_placement(real_case):
    """Same rule, mirrored side: medial_x < lateral_x on the left."""
    volume, masks, hand = real_case
    tv, _ = mask_to_mesh(
        masks["tibia_L"].mask, volume.spacing, volume.origin, volume.direction,
    )
    fv, _ = mask_to_mesh(
        masks["fibula_L"].mask, volume.spacing, volume.origin, volume.direction,
    )
    centre, info = ankle_centre(tv, fv)

    tibia_z_min = float(tv[:, 2].min())
    assert info["plafond_z"] > tibia_z_min + 10.0, (
        f"plafond_z={info['plafond_z']:.1f} is too close to tibia bottom "
        f"{tibia_z_min:.1f}; picked the malleolar tip, not the plafond"
    )
    assert info["medial_x"] < info["lateral_x"], (
        f"on the left side medial should be less than lateral; "
        f"got medial_x={info['medial_x']:.1f}, "
        f"lateral_x={info['lateral_x']:.1f}"
    )
    reference = np.array(hand["ankle_centre_L"])
    error_mm = float(np.linalg.norm(centre - reference))
    assert error_mm < 6.0, (
        f"ankle error {error_mm:.2f} mm; auto {centre.round(1)} vs "
        f"hand {reference.round(1)}; info={info}"
    )


def test_knee_centre_right_agrees_with_hand_placement(real_case):
    """Notch-based knee centre; error under 15 mm.
    
    The 15 mm threshold is generous because the notch rule falls back 
    to the condyle midpoint if it cannot find an intercondylar gap.
    """
    volume, masks, hand = real_case
    fv, _ = mask_to_mesh(
        masks["femur_R"].mask, volume.spacing, volume.origin, volume.direction,
    )
    tv, _ = mask_to_mesh(
        masks["tibia_R"].mask, volume.spacing, volume.origin, volume.direction,
    )
    centre, info = knee_centre(fv, tv)

    assert info["condyle_medial"][0] > info["condyle_lateral"][0], (
        f"on the right side medial should exceed lateral in LPS x; "
        f"got medial x={info['condyle_medial'][0]:.1f}, "
        f"lateral x={info['condyle_lateral'][0]:.1f}"
    )
    separation_mm = float(
        np.linalg.norm(info["condyle_medial"] - info["condyle_lateral"])
    )
    assert separation_mm > 20.0, (
        f"condyles only {separation_mm:.1f} mm apart; "
        f"the half-split did not find two distinct blobs"
    )
    reference = np.array(hand["knee_centre_R"])
    error_mm = float(np.linalg.norm(centre - reference))
    assert error_mm < 15.0, (
        f"knee centre error {error_mm:.2f} mm; auto {centre.round(1)} vs "
        f"hand {reference.round(1)}; info={ {k: v.round(1) if hasattr(v, 'round') else v for k, v in info.items()} }"
    )


def test_knee_centre_left_agrees_with_hand_placement(real_case):
    """Same rule, mirrored side: medial x < lateral x on the left."""
    volume, masks, hand = real_case
    fv, _ = mask_to_mesh(
        masks["femur_L"].mask, volume.spacing, volume.origin, volume.direction,
    )
    tv, _ = mask_to_mesh(
        masks["tibia_L"].mask, volume.spacing, volume.origin, volume.direction,
    )
    centre, info = knee_centre(fv, tv)

    assert info["condyle_medial"][0] < info["condyle_lateral"][0], (
        f"on the left side medial should be less than lateral in LPS x; "
        f"got medial x={info['condyle_medial'][0]:.1f}, "
        f"lateral x={info['condyle_lateral'][0]:.1f}"
    )
    separation_mm = float(
        np.linalg.norm(info["condyle_medial"] - info["condyle_lateral"])
    )
    assert separation_mm > 20.0, (
        f"condyles only {separation_mm:.1f} mm apart; "
        f"the half-split did not find two distinct blobs"
    )
    reference = np.array(hand["knee_centre_L"])
    error_mm = float(np.linalg.norm(centre - reference))
    assert error_mm < 15.0, (
        f"knee centre error {error_mm:.2f} mm; auto {centre.round(1)} vs "
        f"hand {reference.round(1)}; info={ {k: v.round(1) if hasattr(v, 'round') else v for k, v in info.items()} }"
    )