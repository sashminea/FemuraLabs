#!/usr/bin/env python3
"""Train a 3D SegResNet on the full-volume .npy files written by prepare_dataset.py.

Example (Kaggle):
    pip install monai
    python train.py --data-dir /kaggle/input/femuralabs-npy --out /kaggle/working/run1 \
        --patch 96 --batch-size 2 --init-filters 16

Smoke test on a small local GPU:
    python scripts/ml/train.py --data-dir data/ml_npy --out runs/smoke --patch 64 \
        --batch-size 1 --init-filters 8 --epochs 2 --iters-per-epoch 5 --val-every 1 --num-workers 0

Defaults for epochs, iterations, learning rate and augmentation are untuned starting
points. Training sessions on free GPUs get cut off: rerun the same command with --resume
to continue from <out>/last.pt.

Side merging: with --merge-sides (default) the model predicts 4 bone classes
(femur, tibia, fibula, talus) and left-right flip augmentation is on. With
--no-merge-sides it predicts the 8 original labels and flips are off (a flip would
turn a right bone into a left bone without swapping its label).
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import random
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F
from monai.losses import DiceCELoss
from torch.utils.data import DataLoader, Dataset

from common import (HU_MAX, HU_MIN, PatchSampler, apply_label_map, build_model, class_names,
                    dice_per_class, normalize_hu, num_classes, predict_volume)


class CropDataset(Dataset):
    """Endless random crops; the index is ignored, each worker has its own RNG stream."""

    def __init__(self, sampler: PatchSampler, length: int):
        self.sampler = sampler
        self.length = length
        self._rng = None

    def __len__(self) -> int:
        return self.length

    def __getitem__(self, _):
        if self._rng is None:
            self._rng = np.random.default_rng(torch.initial_seed() % (2 ** 32))
        ct, seg = self.sampler.sample(self._rng)
        return torch.from_numpy(ct)[None], torch.from_numpy(seg)[None]


def _random_theta(max_rot_deg: float, smin: float, smax: float) -> torch.Tensor:
    """3x4 affine for F.affine_grid: random rotation about each axis and isotropic scale."""
    r = math.radians(max_rot_deg)
    ax, ay, az = (random.uniform(-r, r) for _ in range(3))
    cx, sx, cy, sy, cz, sz = math.cos(ax), math.sin(ax), math.cos(ay), math.sin(ay), math.cos(az), math.sin(az)
    rx = torch.tensor([[1.0, 0, 0], [0, cx, -sx], [0, sx, cx]])
    ry = torch.tensor([[cy, 0, sy], [0, 1.0, 0], [-sy, 0, cy]])
    rz = torch.tensor([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1.0]])
    m = (rz @ ry @ rx) / random.uniform(smin, smax)
    return torch.cat([m, torch.zeros(3, 1)], dim=1)


def gpu_augment(x: torch.Tensor, y: torch.Tensor, a: argparse.Namespace):
    """x: (B,1,P,P,P) float in [0,1]; y: (B,1,P,P,P) long. Returns augmented (x, y)."""
    b = x.shape[0]
    if a.merge_sides and not a.no_flip:
        for i in range(b):  # array axis 2 (last) is image x, i.e. left-right
            if random.random() < 0.5:
                x[i] = x[i].flip(-1)
                y[i] = y[i].flip(-1)
    if a.affine_prob > 0:
        thetas = [
            _random_theta(a.max_rot_deg, a.scale_min, a.scale_max) if random.random() < a.affine_prob
            else torch.eye(3, 4)
            for _ in range(b)
        ]
        theta = torch.stack(thetas).to(x.device, x.dtype)
        grid = F.affine_grid(theta, list(x.shape), align_corners=False)
        x = F.grid_sample(x, grid, mode="bilinear", padding_mode="zeros", align_corners=False)
        y = F.grid_sample(y.float(), grid, mode="nearest", padding_mode="zeros",
                          align_corners=False).long()
    scale = torch.empty(b, 1, 1, 1, 1, device=x.device).uniform_(0.9, 1.1)
    shift = torch.empty(b, 1, 1, 1, 1, device=x.device).uniform_(-0.05, 0.05)
    x = (x * scale + shift + 0.01 * torch.randn_like(x)).clamp_(0.0, 1.0)
    return x, y


def evaluate(model, val_data, a, device, n_classes):
    """Mean Dice over val cases and classes, computed on the resampled grid (for model selection only)."""
    per_case = {}
    for case, ct, seg in val_data:
        pred = predict_volume(model, ct, a.patch, a.sw_batch_size, a.overlap, device)
        per_case[case] = dice_per_class(pred, seg, n_classes)
    values = [d for dice in per_case.values() for d in dice.values()]
    return float(np.nanmean(values)), per_case


def save_checkpoint(path, model, opt, sched, scaler, epoch, best, config):
    torch.save({"model": model.state_dict(), "optimizer": opt.state_dict(),
                "scheduler": sched.state_dict(), "scaler": scaler.state_dict(),
                "epoch": epoch, "best_val_dice": best, "config": config}, path)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--data-dir", type=Path, required=True, help="folder with caseXX_ct.npy / caseXX_seg.npy")
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--train-cases", default="case01,case02,case03,case04,case05,case06")
    p.add_argument("--val-cases", default="case07,case08")
    p.add_argument("--merge-sides", action=argparse.BooleanOptionalAction, default=True)
    p.add_argument("--patch", type=int, default=96)
    p.add_argument("--batch-size", type=int, default=2)
    p.add_argument("--init-filters", type=int, default=16)
    p.add_argument("--epochs", type=int, default=100)
    p.add_argument("--iters-per-epoch", type=int, default=100)
    p.add_argument("--lr", type=float, default=3e-4)
    p.add_argument("--weight-decay", type=float, default=1e-5)
    p.add_argument("--fg-prob", type=float, default=0.67, help="fraction of crops centred on a bone")
    p.add_argument("--num-workers", type=int, default=2)
    p.add_argument("--val-every", type=int, default=5)
    p.add_argument("--sw-batch-size", type=int, default=2)
    p.add_argument("--overlap", type=float, default=0.5)
    p.add_argument("--affine-prob", type=float, default=0.5)
    p.add_argument("--max-rot-deg", type=float, default=15.0)
    p.add_argument("--scale-min", type=float, default=0.85)
    p.add_argument("--scale-max", type=float, default=1.15)
    p.add_argument("--no-flip", action="store_true", help="disable left-right flips")
    p.add_argument("--no-amp", action="store_true")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--resume", action="store_true")
    a = p.parse_args(argv)

    if a.patch % 8 != 0:
        raise SystemExit("--patch must be a multiple of 8 (SegResNet downsamples 3 times)")
    random.seed(a.seed)
    np.random.seed(a.seed)
    torch.manual_seed(a.seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    use_amp = device.type == "cuda" and not a.no_amp
    n_classes = num_classes(a.merge_sides)
    names = class_names(a.merge_sides)
    train_cases = [c for c in a.train_cases.split(",") if c]
    val_cases = [c for c in a.val_cases.split(",") if c]
    a.out.mkdir(parents=True, exist_ok=True)

    for case in train_cases + val_cases:
        for kind in ("ct", "seg"):
            if not (a.data_dir / f"{case}_{kind}.npy").exists():
                raise SystemExit(f"missing {a.data_dir / f'{case}_{kind}.npy'}")

    config = {k: (str(v) if isinstance(v, Path) else v) for k, v in vars(a).items()}
    config.update({"hu_min": HU_MIN, "hu_max": HU_MAX, "n_classes": n_classes})
    (a.out / "run_config.json").write_text(json.dumps(config, indent=2))

    sampler = PatchSampler(a.data_dir, train_cases, a.patch, a.merge_sides, fg_prob=a.fg_prob)
    dataset = CropDataset(sampler, a.iters_per_epoch * a.batch_size)
    loader = DataLoader(dataset, batch_size=a.batch_size, shuffle=False, num_workers=a.num_workers,
                        pin_memory=device.type == "cuda", drop_last=True,
                        persistent_workers=a.num_workers > 0)
    val_data = [(c, np.load(a.data_dir / f"{c}_ct.npy"),
                 apply_label_map(np.load(a.data_dir / f"{c}_seg.npy"), a.merge_sides))
                for c in val_cases]

    model = build_model(a.init_filters, n_classes).to(device)
    n_params = sum(q.numel() for q in model.parameters() if q.requires_grad)
    opt = torch.optim.AdamW(model.parameters(), lr=a.lr, weight_decay=a.weight_decay)
    total_steps = a.epochs * a.iters_per_epoch
    sched = torch.optim.lr_scheduler.LambdaLR(opt, lambda s: max(0.0, 1.0 - s / total_steps) ** 0.9)
    scaler = torch.amp.GradScaler("cuda", enabled=use_amp)
    loss_fn = DiceCELoss(to_onehot_y=True, softmax=True)

    start_epoch, best = 1, -1.0
    last_path, best_path, csv_path = a.out / "last.pt", a.out / "best.pt", a.out / "metrics.csv"
    if a.resume and last_path.exists():
        ck = torch.load(last_path, map_location=device, weights_only=True)
        model.load_state_dict(ck["model"])
        opt.load_state_dict(ck["optimizer"])
        sched.load_state_dict(ck["scheduler"])
        scaler.load_state_dict(ck["scaler"])
        start_epoch, best = ck["epoch"] + 1, ck["best_val_dice"]
        print(f"resumed from {last_path} at epoch {start_epoch}, best val Dice {best:.4f}")
    elif a.resume:
        print(f"--resume given but {last_path} not found; starting from scratch")

    fields = ["epoch", "train_loss", "lr", "seconds", "val_mean_dice"] + \
             [f"{c}_{names[k]}" for c in val_cases for k in range(1, n_classes)]
    print(f"device={device} amp={use_amp} classes={n_classes} params={n_params:,} "
          f"train={train_cases} val={val_cases} patch={a.patch} batch={a.batch_size}")

    for epoch in range(start_epoch, a.epochs + 1):
        t0 = time.time()
        model.train()
        running, n_batches = 0.0, 0
        for ct, seg in loader:
            x = normalize_hu(ct.to(device, non_blocking=True))
            y = seg.to(device, non_blocking=True).long()
            x, y = gpu_augment(x, y, a)
            opt.zero_grad(set_to_none=True)
            with torch.autocast(device_type=device.type, dtype=torch.float16, enabled=use_amp):
                logits = model(x)
            loss = loss_fn(logits.float(), y)
            scaler.scale(loss).backward()
            scaler.unscale_(opt)
            torch.nn.utils.clip_grad_norm_(model.parameters(), 12.0)
            scaler.step(opt)
            scaler.update()
            sched.step()
            running += loss.item()
            n_batches += 1

        row = {"epoch": epoch, "train_loss": round(running / max(n_batches, 1), 5),
               "lr": f"{sched.get_last_lr()[0]:.2e}"}
        msg = f"epoch {epoch:3d}/{a.epochs}  loss {row['train_loss']:.4f}"
        if epoch % a.val_every == 0 or epoch == a.epochs:
            mean_dice, per_case = evaluate(model, val_data, a, device, n_classes)
            row["val_mean_dice"] = round(mean_dice, 4)
            for c, dice in per_case.items():
                for k, v in dice.items():
                    row[f"{c}_{names[k]}"] = round(v, 4)
            msg += f"  val Dice {mean_dice:.4f}  " + "  ".join(
                f"{c}:{np.nanmean(list(d.values())):.3f}" for c, d in per_case.items())
            if mean_dice > best:
                best = mean_dice
                save_checkpoint(best_path, model, opt, sched, scaler, epoch, best, config)
                msg += "  <- best"
        row["seconds"] = round(time.time() - t0, 1)
        save_checkpoint(last_path, model, opt, sched, scaler, epoch, best, config)
        is_new = not csv_path.exists()
        with open(csv_path, "a", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields, restval="")
            if is_new:
                w.writeheader()
            w.writerow(row)
        print(msg + f"  ({row['seconds']}s)", flush=True)

    print(f"done. best val Dice (resampled grid) {best:.4f}; checkpoints in {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())