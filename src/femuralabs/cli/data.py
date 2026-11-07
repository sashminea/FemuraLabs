import typer
from pathlib import Path
from femuralabs.cli.utils import run_script, console

app = typer.Typer()

@app.command()
def inventory(dir: Path = typer.Option(..., "--dir", "-d", help="Directory to scan")):
    """Scan a directory for DICOM/NRRD/NIfTI files and list them."""
    run_script("scripts/dev/inventory_dataset.py", ["--dir", str(dir)])

@app.command()
def merge(
    thighs: Path = typer.Option(..., help="Path to thighs NIfTI"),
    shanks: Path = typer.Option(..., help="Path to shanks NIfTI"),
    out: Path = typer.Option(..., help="Output combined_seg.nii")
):
    """Merge Slicer-exported thighs and shanks into an 8-label combined mask."""
    run_script("scripts/data/merge_segmentation.py", ["--thighs", str(thighs), "--shanks", str(shanks), "--out", str(out)])

@app.command()
def preprocess(
    ct: Path = typer.Option(..., help="Full-body CT (.nii)"),
    thighs_seg: Path = typer.Option(..., help="Thighs seg (.seg.nrrd)"),
    shanks_seg: Path = typer.Option(..., help="Shanks seg (.seg.nrrd)"),
    transform: Path = typer.Option(..., help="H5 transform file"),
    out_dir: Path = typer.Option(..., help="Output directory")
):
    """Apply H5 transform, crop, and center a full-body subject."""
    run_script("scripts/data/process_full_body_raw.py", [
        "--ct", str(ct), "--thighs-seg", str(thighs_seg), 
        "--shanks-seg", str(shanks_seg), "--transform", str(transform), 
        "--out-dir", str(out_dir)
    ])