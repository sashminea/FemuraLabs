import typer
from pathlib import Path
import numpy as np
from rich.console import Console
from rich.table import Table

from femuralabs.toolkit.imaging.volume_info import describe, make_volume
from femuralabs.toolkit.reporting.report import write_info

app = typer.Typer()
console = Console()

@app.command()
def info(
    file: Path = typer.Option(None, "--file", "-f", help="Path to a .npy volume. Omit to generate a synthetic one."),
    shape: tuple[int, int, int] = typer.Option((4, 6, 6), "--shape", help="Shape for synthetic volume (z y x)"),
    spacing: tuple[float, float, float] = typer.Option((2.0, 1.0, 1.0), "--spacing", help="Spacing for synthetic volume (z y x)"),
    out: Path = typer.Option(None, "--out", help="Folder to write info.json")
):
    """Print the geometry of a synthetic or saved volume."""
    if file:
        vol = np.load(file)
    else:
        vol, _ = make_volume(shape)

    info_dict = describe(vol, spacing)
    
    table = Table(title="Volume Geometry")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Shape (z, y, x)", str(info_dict["shape"]))
    table.add_row("Spacing (mm)", str(info_dict["spacing"]))
    table.add_row("Dtype", str(info_dict["dtype"]))
    table.add_row("Extent (mm)", str(info_dict["extent_mm"]))
    console.print(table)

    if out:
        path = write_info(info_dict, out)
        console.print(f"[bold green]Wrote info to {path}[/bold green]")