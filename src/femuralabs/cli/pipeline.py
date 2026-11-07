import typer
from pathlib import Path
from femuralabs.cli.utils import run_script, console

app = typer.Typer()

@app.command()
def run(
    case: Path = typer.Option(..., help="Path to combined_seg.nii"),
    out: Path = typer.Option(..., help="Output directory"),
    compare: Path = typer.Option(None, help="Optional path to landmarks.mrk.json"),
    angles: bool = typer.Option(False, help="Compute alignment angles"),
    fill: bool = typer.Option(False, help="Fill medullary canals before meshing")
):
    """Run mesh extraction, landmarks, and angles for one case."""
    args = ["--case", str(case), "--out", str(out)]
    if compare: args += ["--compare", str(compare)]
    if angles: args += ["--angles"]
    if fill: args += ["--fill-interior"]
    run_script("scripts/pipeline/pipeline_demo.py", args)

@app.command()
def batch(
    data_dir: Path = typer.Option(Path("data/raw"), help="Directory containing case folders"),
    out_dir: Path = typer.Option(Path("output"), help="Output directory")
):
    """Run the pipeline on all cases in the data directory."""
    console.print("[bold cyan]Starting batch pipeline...[/bold cyan]")
    run_script("scripts/pipeline/run_all_cases.py", [])

@app.command()
def report():
    """Generate markdown tables from the JSON outputs."""
    run_script("scripts/pipeline/make_report_tables.py", [])