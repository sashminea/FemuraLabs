import typer
from rich.console import Console
from femuralabs.cli import data, pipeline, ml, doctor
from femuralabs.cli import data, pipeline, ml, doctor, volume

app = typer.Typer(
    name="femuralabs",
    help="Lower-limb CT analysis pipeline and ML segmentation.",
    no_args_is_help=True,
)
console = Console()

app.add_typer(data.app, name="data", help="Dataset preparation and merging.")
app.add_typer(pipeline.app, name="pipeline", help="Geometry, landmarks, and angles.")
app.add_typer(ml.app, name="ml", help="Machine learning training and validation.")
app.add_typer(doctor.app, name="doctor", help="Check system dependencies and environment.")
app.add_typer(volume.app, name="volume", help="Volume geometry and synthetic data.")

@app.command()
def version():
    """Print the current version of FemuraLabs."""
    console.print("FemuraLabs [bold green]v0.1.0[/bold green]")

if __name__ == "__main__":
    app()