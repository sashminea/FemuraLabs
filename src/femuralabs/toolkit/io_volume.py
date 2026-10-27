"""Load and save volumes with correct geometry."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import SimpleITK as sitk

@dataclass(frozen=True)
class Volume:
    """A volume array plus the geometry fields SimpleITK exposes.

    array is (z, y, x). spacing, origin and direction are in (x, y, z)
    order as SimpleITK returns them.
    """
    array: np.ndarray
    spacing: tuple[float, float, float]
    origin: tuple[float, float, float]
    direction: tuple[float, ...] # 9 values, row-major


def load_volume(path: Path | str) -> Volume:
    """Read a NRRD or NIfTI volume; return array and geometry.

    The array in the returned Volume is (z, y, x). SimpleITK's
    GetSize() returns (x, y, z), so array.shape == image.GetSize()[::-1]
    """

    image = sitk.ReadImage(str(path))
    return Volume(
        array=sitk.GetArrayFromImage(image),
        spacing=tuple(image.GetSpacing()),
        origin=tuple(image.GetOrigin()),
        direction=tuple(image.GetDirection()),
    )

def save_nifti(volume: Volume, path: Path | str) -> None:
    """Write a Volume to NIfTI, preserving spacing, origin, direction/

    .nii writes uncompressed; .nii.gz writes gzipped.
    """
    image = sitk.GetImageFromArray(volume.array)
    image.SetSpacing(volume.spacing)
    image.SetOrigin(volume.origin)
    image.SetDirection(volume.direction)
    sitk.WriteImage(image, str(path))

