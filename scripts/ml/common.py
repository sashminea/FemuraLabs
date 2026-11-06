"""Shared helpers for train.py and validate.py.

Everything that needs only numpy lives at the top and imports without torch.
Keep HU_MIN/HU_MAX, the label maps and the model builder here and nowhere else:
training and validation must agree on them exactly.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

# ---- intensity window -------------------------------------------------------
# Raw HU is stored as int16 and windowed on the fly.  In all 8 cases the 75th
# percentile of labelled voxels is above 1100 HU, so the old [-1000, 1000] window
# saturated at least a quarter of them; this window keeps more cortical contrast
# and still contains soft tissue and fat comfortably.
HU_MIN = -500.0
HU_MAX = 1500.0
HU_AIR_INT = -1024  # padding value for CT crops

# ---- labels -----------------------------------------------------------------
LABEL_NAMES_8 = {
    1: "femur_R", 2: "femur_L", 3: "tibia_R", 4: "tibia_L",
    5: "fibula_R", 6: "fibula_L", 7: "talus_R", 8: "talus_L",
}
MERGED_NAMES = {1: "femur", 2: "tibia", 3: "fibula", 4: "talus"}
# index = 8-label id, value = merged class id (sides merged)
MERGE_LUT = np.array([0, 1, 1, 2, 2, 3, 3, 4, 4], dtype=np.uint8)


def num_classes(merge_sides: bool) -> int:
    """Output channels including background."""
    return 5 if merge_sides else 9


def class_names(merge_sides: bool) -> dict[int, str]:
    return dict(MERGED_NAMES if merge_sides else LABEL_NAMES_8)


def apply_label_map(seg: np.ndarray, merge_sides: bool) -> np.ndarray:
    """8-label array -> training labels (uint8)."""
    return MERGE_LUT[seg] if merge_sides else seg


# ---- patch sampling (numpy only, so it can be tested without torch) ---------
def crop_with_pad(arr: np.ndarray, start: np.ndarray, size: int, fill) -> np.ndarray:
    """Cube of side `size` whose corner is `start`; anything outside `arr` is `fill`."""
    start = np.asarray(start, dtype=np.int64)
    out = np.full((size, size, size), fill, dtype=arr.dtype)
    src_lo = np.maximum(start, 0)
    src_hi = np.minimum(start + size, np.array(arr.shape))
    if np.any(src_hi <= src_lo):
        return out
    dst_lo = src_lo - start
    dst_hi = dst_lo + (src_hi - src_lo)
    out[dst_lo[0]:dst_hi[0], dst_lo[1]:dst_hi[1], dst_lo[2]:dst_hi[2]] = \
        arr[src_lo[0]:src_hi[0], src_lo[1]:src_hi[1], src_lo[2]:src_hi[2]]
    return out


class PatchSampler:
    """Random cubic crops from the full-volume .npy files.

    With probability fg_prob a patch is centred (plus jitter) on a random voxel of
    a randomly chosen foreground class, so every class is seen equally often; otherwise
    the centre is uniform over the whole volume, which also produces background-only
    patches. Volumes are memory-mapped and opened lazily, so this is safe to copy
    into DataLoader workers.
    """

    def __init__(self, data_dir, cases, patch: int, merge_sides: bool,
                 fg_prob: float = 0.67, jitter_frac: float = 0.25, max_seeds: int = 20000):
        self.data_dir = Path(data_dir)
        self.cases = list(cases)
        self.patch = int(patch)
        self.merge_sides = merge_sides
        self.fg_prob = fg_prob
        self.jitter = int(self.patch * jitter_frac)
        self._mm: dict = {}
        self.seeds: dict[str, list[np.ndarray]] = {}
        init_rng = np.random.default_rng(0)
        for case in self.cases:
            seg = apply_label_map(np.load(self.data_dir / f"{case}_seg.npy"), merge_sides)
            per_class = []
            for k in range(1, num_classes(merge_sides)):
                idx = np.argwhere(seg == k)
                if len(idx) > max_seeds:
                    idx = idx[init_rng.choice(len(idx), max_seeds, replace=False)]
                if len(idx):
                    per_class.append(idx.astype(np.int32))
            if not per_class:
                raise ValueError(f"{case}: no labelled voxels after label mapping")
            self.seeds[case] = per_class
            del seg

    def _open(self, case: str):
        if case not in self._mm:
            self._mm[case] = (
                np.load(self.data_dir / f"{case}_ct.npy", mmap_mode="r"),
                np.load(self.data_dir / f"{case}_seg.npy", mmap_mode="r"),
            )
        return self._mm[case]

    def sample(self, rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
        """Return (ct int16, seg uint8), each (P, P, P)."""
        case = self.cases[int(rng.integers(len(self.cases)))]
        ct, seg = self._open(case)
        if rng.random() < self.fg_prob:
            classes = self.seeds[case]
            seeds = classes[int(rng.integers(len(classes)))]
            centre = seeds[int(rng.integers(len(seeds)))].astype(np.int64)
            centre = centre + rng.integers(-self.jitter, self.jitter + 1, size=3)
        else:
            centre = np.array([int(rng.integers(s)) for s in ct.shape], dtype=np.int64)
        start = centre - self.patch // 2
        ct_c = crop_with_pad(ct, start, self.patch, HU_AIR_INT)
        seg_c = crop_with_pad(seg, start, self.patch, 0)
        return ct_c, apply_label_map(seg_c, self.merge_sides)


# ---- metrics ----------------------------------------------------------------
def dice_per_class(pred: np.ndarray, target: np.ndarray, n_classes: int) -> dict[int, float]:
    """Dice for classes 1..n_classes-1; NaN if the class is absent from both."""
    out = {}
    for c in range(1, n_classes):
        p, t = pred == c, target == c
        denom = int(p.sum()) + int(t.sum())
        out[c] = float(2.0 * int((p & t).sum()) / denom) if denom > 0 else float("nan")
    return out


# ---- torch-dependent helpers ------------------------------------------------
def normalize_hu(x):
    """int16/float HU tensor -> float32 in [0, 1] using the fixed window."""
    x = x.float().clamp(HU_MIN, HU_MAX)
    return (x - HU_MIN) / (HU_MAX - HU_MIN)


def build_model(init_filters: int, n_classes: int):
    from monai.networks.nets import SegResNet
    if init_filters % 8 != 0:
        raise ValueError("init_filters must be a multiple of 8 (SegResNet uses 8 norm groups)")
    return SegResNet(spatial_dims=3, in_channels=1, out_channels=n_classes, init_filters=init_filters)


def predict_volume(model, hu_vol: np.ndarray, roi: int, sw_batch_size: int,
                   overlap: float, device) -> np.ndarray:
    """Sliding-window inference on one whole int16 HU volume -> uint8 class map (z, y, x)."""
    import torch
    from monai.inferers import sliding_window_inference

    model.eval()
    with torch.no_grad():
        x = normalize_hu(torch.from_numpy(hu_vol).to(device))[None, None]
        with torch.autocast(device_type=device.type, dtype=torch.float16,
                            enabled=device.type == "cuda"):
            logits = sliding_window_inference(
                x, roi_size=(roi, roi, roi), sw_batch_size=sw_batch_size,
                predictor=lambda t: model(t).float(), overlap=overlap, mode="gaussian",
            )
        return logits.argmax(dim=1)[0].to(torch.uint8).cpu().numpy()