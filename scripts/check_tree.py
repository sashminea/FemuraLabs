"""Check that the files the project claims to have are actually on disk."""
from pathlib import Path

REQUIRED = [
    "Dockerfile",
    "requirements-tool.txt",
    ".dockerignore",
    "scripts/check_tree.py",
    "docs/INVENTORY.md",
    "docs/DECISIONS.md",
    "docs/RUNBOOK.md",
    "AGENTS.md",
    "docs/FLOW.md",
    "docs/flow",
    "docker-compose.yml",
    "web/index.html",
]


def main() -> int:
    missing = [p for p in REQUIRED if not Path(p).exists()]
    for p in REQUIRED:
        print("MISSING" if p in missing else "ok     ", p)
    print(f"{len(missing)} missing" if missing else "all present")
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())