import os
import subprocess
from pathlib import Path
from rich.console import Console

console = Console()

def run_script(script_path: str, args: list[str]):
    """Run a python script with PYTHONPATH=src configured."""
    env = {**os.environ, "PYTHONPATH": "src"}
    cmd = ["python", script_path] + args
    
    console.print(f"[dim]Running: {script_path} {' '.join(args)}[/dim]")
    result = subprocess.run(cmd, env=env)
    if result.returncode != 0:
        console.print(f"[bold red]Command failed with exit code {result.returncode}[/bold red]")
        raise SystemExit(result.returncode)