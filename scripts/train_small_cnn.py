"""Train SmallCNN on MNIST, log per epoch, save best checkpoint, plot curves."""

from __future__ import annotations

import argparse
from pathlib import Path

import torch
from torch import nn
from torch.utils.data import DataLoader, random_split
from torchvision import datasets, transforms

from femuralabs.toolkit.training.model import SmallCNN
from femuralabs.toolkit.training.train_utils import (
    append_row,
    environment_record,
    evaluate_with_accuracy,
    get_device,
    plot_curves,
    save_checkpoint,
    save_config,
    set_seed,
    train_one_epoch,
)

def build_loaders(batch_size: int, seed: int, data_root: Path):
    tfm = transforms.Compose(
        [
            transforms.ToTensor(),
            transforms.Normalize((0.1307,), (0.3081,)),
        ]
    )
    full = datasets.MNIST(data_root, train=True, download=True, transform=tfm)

    gen = torch.Generator().manual_seed(seed)
    train_set, val_set = random_split(full, [54000, 6000], generator=gen)

    train_loader = DataLoader(
        train_set, batch_size=batch_size, shuffle=True, num_workers=0, generator=gen
    )
    val_loader = DataLoader(val_set, batch_size=256, shuffle=False, num_workers=0)
    return train_loader, val_loader


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Train SmallCNN on MNIST.")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--lr", type=float, default=0.01)
    parser.add_argument("--run-name", type=str, default="run_a")
    parser.add_argument("--commit", type=str, default="unknown",
                    help='git describe --always --dirty; "unknown" when not supplied')
    args = parser.parse_args(argv)

    set_seed(args.seed)
    device = get_device()



    run_dir = Path("runs") / args.run_name
    run_dir.mkdir(parents=True, exist_ok=True)
    save_config(run_dir / "config.json", vars(args))
    gpu = "none"
    
    if device.type == "cuda":
        import torch as _torch
        gpu = _torch.cuda.get_device_name(0)
    save_config(run_dir / "environment.json", environment_record(gpu=gpu))  

    train_loader, val_loader = build_loaders(args.batch_size, args.seed, Path("data"))

    model = SmallCNN().to(device)
    loss_fn = nn.CrossEntropyLoss()
    optimizer = torch.optim.SGD(model.parameters(), lr=args.lr, momentum=0.9)

    best = float("inf")

    for epoch in range(1, args.epochs + 1):
        train_loss = train_one_epoch(model, train_loader, loss_fn, optimizer, device)
        val_loss, acc = evaluate_with_accuracy(model, val_loader, loss_fn, device)

        append_row(
            run_dir / "metrics.csv",
            {
                "epoch": epoch,
                "train_loss": round(train_loss, 6),
                "val_loss": round(val_loss, 6),
                "accuracy": round(acc, 6),
            },
        )
        print(
            f"epoch {epoch}: train {train_loss:.4f} val {val_loss:.4f} acc {acc:.4f}"
        )

        if val_loss < best:
            best = val_loss
            save_checkpoint(
                run_dir / "best.pt", model, optimizer, epoch, best, vars(args)
            )

    plot_curves(run_dir / "metrics.csv", Path("reports") / f"{args.run_name}_curves.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())