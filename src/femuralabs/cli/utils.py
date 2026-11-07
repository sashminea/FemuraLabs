import os
import subprocess
from pathlib import Path
from rich.console import Console

console = Console()

# Resolve the repo root from the location of this file (src/femuralabs/cli/utils.py -> parents[3])
REPO_ROOT = Path(__file__).resolve().parents[3]

def run_script(script_path: str, args: list[str]):
    """Run a python script with PYTHONPATH configured and CWD set to the repo root."""
    full_script_path = REPO_ROOT / script_path
    if not full_script_path.exists():
        console.print(f"[bold red]Error: Script not found at {full_script_path}[/bold red]")
        raise SystemExit(1)

    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")}
    
    # Ensure scripts/ml can find common.py
    if "scripts/ml" in script_path or "scripts/ml" in str(full_script_path):
        env["PYTHONPATH"] += os.pathsep + str(REPO_ROOT / "scripts" / "ml")

    cmd = ["python", str(full_script_path)] + args

    console.print(f"[dim]Running: {script_path} {' '.join(args)}[/dim]")
    # Set cwd to REPO_ROOT so relative paths in scripts (like data/raw) work
    result = subprocess.run(cmd, env=env, cwd=REPO_ROOT)
    
    if result.returncode != 0:
        console.print(f"[bold red]Command failed with exit code {result.returncode}[/bold red]")
        raise SystemExit(result.returncode)