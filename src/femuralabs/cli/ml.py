import typer
import urllib.request
import zipfile
from pathlib import Path
from femuralabs.cli.utils import run_script, console

app = typer.Typer()

# The exact URL to your GitHub Release asset
WEIGHTS_URL = "https://github.com/sashminea/FemuraLabs/releases/download/v1.0.0-weights/femuralabs_segresnet_v1.pt"
DEFAULT_WEIGHTS_DIR = Path.home() / ".femuralabs" / "weights"
DEFAULT_WEIGHTS_PATH = DEFAULT_WEIGHTS_DIR / "femuralabs_segresnet_v1.pt"

@app.command()
def download_weights():
    """Download the pretrained SegResNet weights from the GitHub Release."""
    DEFAULT_WEIGHTS_DIR.mkdir(parents=True, exist_ok=True)
    console.print(f"Downloading weights from [cyan]{WEIGHTS_URL}[/cyan]...")
    
    temp_path = DEFAULT_WEIGHTS_DIR / "temp_download"
    
    def report_hook(block_num, block_size, total_size):
        if total_size > 0:
            percent = min(100, (block_num * block_size * 100) // total_size)
            console.print(f"\rDownloading: [green]{percent}%[/green]", end="")
            
    try:
        urllib.request.urlretrieve(WEIGHTS_URL, temp_path, reporthook=report_hook)
        console.print()
        
        # Handle the case where the user uploaded a .zip instead of a .pt
        if zipfile.is_zipfile(temp_path):
            console.print("Extracting zip file...")
            with zipfile.ZipFile(temp_path, 'r') as zip_ref:
                zip_ref.extractall(DEFAULT_WEIGHTS_DIR)
            temp_path.unlink()
        else:
            temp_path.rename(DEFAULT_WEIGHTS_PATH)
            
        console.print(f"[bold green]Weights saved to {DEFAULT_WEIGHTS_PATH}[/bold green]")
    except Exception as e:
        console.print(f"[bold red]Download failed: {e}[/bold red]")
        if temp_path.exists():
            temp_path.unlink()

@app.command()
def prepare(
    out_dir: Path = typer.Option(Path("data/ml_npy"), help="Output directory for .npy files"),
    spacing: float = typer.Option(1.5, help="Isotropic resampling spacing (mm)")
):
    """Extract, fill, and resample full volumes to .npy for ML training."""
    run_script("scripts/ml/prepare_dataset.py", ["--out", str(out_dir), "--spacing", str(spacing)])

@app.command()
def train(
    data_dir: Path = typer.Option(..., help="Directory containing .npy files"),
    out_dir: Path = typer.Option(..., help="Output directory for checkpoints"),
    patch: int = typer.Option(96, help="Patch size"),
    batch_size: int = typer.Option(2, help="Batch size"),
    epochs: int = typer.Option(200, help="Number of epochs"),
    resume: bool = typer.Option(False, help="Resume from last.pt")
):
    """Train the SegResNet model."""
    args = [
        "--data-dir", str(data_dir), "--out", str(out_dir),
        "--patch", str(patch), "--batch-size", str(batch_size), "--epochs", str(epochs)
    ]
    if resume: args.append("--resume")
    run_script("scripts/ml/train.py", args)

@app.command()
def validate(
    checkpoint: Path = typer.Option(..., help="Path to best.pt"),
    data_dir: Path = typer.Option(..., help="Directory containing .npy files"),
    out_dir: Path = typer.Option(Path("reports/data"), help="Output directory for JSON results"),
    cases: str = typer.Option("case07,case08", help="Comma-separated validation cases")
):
    """Run sliding-window inference and compute Dice/HD95."""
    run_script("scripts/ml/validate.py", [
        "--checkpoint", str(checkpoint), "--data-dir", str(data_dir),
        "--out-dir", str(out_dir), "--val-cases", cases
    ])

@app.command()
def infer(
    ct: Path = typer.Option(..., help="Path to raw CT (.nii or .nrrd)"),
    out: Path = typer.Option(..., help="Output path for combined_seg.nii"),
    checkpoint: Path = typer.Option(DEFAULT_WEIGHTS_PATH, help="Path to model weights")
):
    """Run sliding-window inference on a raw CT to generate a combined_seg.nii file."""
    if not checkpoint.exists():
        console.print(f"[bold red]Checkpoint not found at {checkpoint}[/bold red]")
        console.print("Run [bold cyan]femuralabs ml download-weights[/bold cyan] first, or provide a valid --checkpoint path.")
        raise typer.Exit(1)
        
    run_script("scripts/ml/predict.py", [
        "--checkpoint", str(checkpoint), 
        "--ct", str(ct), 
        "--out", str(out)
    ])

@app.command()
def cv(
    data_dir: Path = typer.Option(..., help="Directory containing .npy files"),
    out_dir: Path = typer.Option(Path("runs/cv"), help="Output directory for folds"),
    epochs: int = typer.Option(100, help="Epochs per fold"),
    patch: int = typer.Option(96, help="Patch size"),
    batch_size: int = typer.Option(2, help="Batch size")
):
    """Run 4-fold cross-validation on the 8 subjects."""
    folds = [
        {"name": "fold1", "train": "case03,case04,case05,case06,case07,case08", "val": "case01,case02"},
        {"name": "fold2", "train": "case01,case02,case05,case06,case07,case08", "val": "case03,case04"},
        {"name": "fold3", "train": "case01,case02,case03,case04,case07,case08", "val": "case05,case06"},
        {"name": "fold4", "train": "case01,case02,case03,case04,case05,case06", "val": "case07,case08"},
    ]

    out_dir.mkdir(parents=True, exist_ok=True)

    for f in folds:
        console.print(f"\n[bold cyan]Starting {f['name']} (Val: {f['val']})[/bold cyan]")
        
        # 1. Train
        console.print(f"--- Training {f['name']} ---")
        train_args = [
            "--data-dir", str(data_dir), "--out", str(out_dir / f["name"]),
            "--train-cases", f["train"], "--val-cases", f["val"],
            "--patch", str(patch), "--batch-size", str(batch_size), "--epochs", str(epochs)
        ]
        run_script("scripts/ml/train.py", train_args)
        
        # 2. Validate
        console.print(f"--- Validating {f['name']} ---")
        val_args = [
            "--checkpoint", str(out_dir / f["name"] / "best.pt"),
            "--data-dir", str(data_dir), "--val-cases", f["val"],
            "--out-dir", str(out_dir / f"{f['name']}_val")
        ]
        run_script("scripts/ml/validate.py", val_args)
        
        console.print(f"[bold green]Finished {f['name']}![/bold green]")