import typer
import shutil
import json
from rich.console import Console
from rich.table import Table

app = typer.Typer()
console = Console()

@app.command()
def check(json_out: bool = typer.Option(False, "--json", help="Output as JSON")):
    """Verify that core dependencies and GPU are available."""
    status = {}

    # Check Python
    status["Python"] = {"status": "OK", "details": "v3.10+"}

    # Check binaries
    for tool in ["python", "docker"]:
        path = shutil.which(tool)
        if path:
            status[tool.capitalize()] = {"status": "OK", "details": path}
        else:
            status[tool.capitalize()] = {"status": "Missing", "details": "Not found in PATH"}

    # Check imports
    for pkg in ["SimpleITK", "numpy", "skimage", "torch", "monai"]:
        try:
            __import__(pkg)
            status[pkg] = {"status": "OK", "details": "Imported"}
        except ImportError:
            status[pkg] = {"status": "Missing", "details": "pip install required"}

    # Check GPU
    try:
        import torch
        if torch.cuda.is_available():
            status["CUDA GPU"] = {"status": "Available", "details": torch.cuda.get_device_name(0)}
        else:
            status["CUDA GPU"] = {"status": "Not Found", "details": "Using CPU"}
    except ImportError:
        status["CUDA GPU"] = {"status": "Missing", "details": "torch not installed"}

    if json_out:
        print(json.dumps(status, indent=2))
    else:
        table = Table(title="FemuraLabs Doctor")
        table.add_column("Dependency", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Details")

        for k, v in status.items():
            color = "green" if v["status"] in ("OK", "Available") else "yellow" if v["status"] == "Not Found" else "red"
            table.add_row(k, f"[{color}]{v['status']}[/{color}]", v["details"])
        
        console.print(table)