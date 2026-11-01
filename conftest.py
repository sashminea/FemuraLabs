import sys
from pathlib import Path
import shutil


sys.path.insert(0, str(Path(__file__).parent / "src"))

def pytest_sessionfinish(session, exitstatus):
    # Clean up the temporary test files so WSL doesn't bloat
    tmp_dir = Path("/tmp/pytest_tmp")
    if tmp_dir.exists():
        shutil.rmtree(tmp_dir, ignore_errors=True)