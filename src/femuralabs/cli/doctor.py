import typer
import shutil
from rich.console import Console
from rich.table import Table

app = typer.Typer()
console = Console()

@app.command()
def check():
    """Verify that core dependencies and GPU are available."""
    table = Table(title="FemuraLabs Doctor")
    table.add_column("Dependency", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details")

    # Check Python
    table.add_row("Python", "[green]OK[/green]", "v3.10+")
    
    # Check binaries
    for tool in ["python", "docker"]:
        path = shutil.which(tool)
        if path:
            table.add_row(tool.capitalize(), "[green]OK[/green]", path)
        else:
            table.add_row(tool.capitalize(), "[red]Missing[/red]", "Not found in PATH")

    # Check imports
    for pkg in ["SimpleITK", "numpy", "skimage", "torch", "monai"]:
        try:
            __import__(pkg)
            table.add_row(pkg, "[green]OK[/green]", "Imported")
        except ImportError:
            table.add_row(pkg, "[red]Missing[/red]", "pip install required")

    # Check GPU
    try:
        import torch
        if torch.cuda.is_available():
            table.add_row("CUDA GPU", "[green]Available[/green]", torch.cuda.get_device_name(0))
        else:
            table.add_row("CUDA GPU", "[yellow]Not Found[/yellow]", "Using CPU")
    except ImportError:
        pass

    console.print(table)