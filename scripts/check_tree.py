"""Check that the files the project claims to have are actually on disk."""
from pathlib import Path

REQUIRED = [
    "Dockerfile",
    "requirements-tool.txt",
    ".dockerignore",
    "scripts/hello_pipeline.py",
    "scripts/check_tree.py",
    "src/femuralabs/toolkit/summary.py",
    "src/femuralabs/toolkit/arrays.py",
    "docs/INVENTORY.md",
    "docs/docker_adaptations.md",
    "docs/RUNBOOK.md",
]


def main() -> int:
    missing = [p for p in REQUIRED if not Path(p).exists()]
    for p in REQUIRED:
        print("MISSING" if p in missing else "ok     ", p)
    print(f"{len(missing)} missing" if missing else "all present")
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())