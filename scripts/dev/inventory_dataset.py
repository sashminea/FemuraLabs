#!/usr/bin/env python3
"""Recursively inventory medical imaging files for a specific subject."""
import argparse
from pathlib import Path

def format_size(bytes_size):
    """Format bytes into a human-readable string (MB/GB)."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} TB"

def main():
    p = argparse.ArgumentParser(description="Audit dataset directories for required files.")
    p.add_argument("--dir", type=Path, required=True, help="Root directory to scan (e.g., D:/Femuralabs/D07)")
    p.add_argument("--filter", type=str, default="", help="Optional substring to filter by (e.g., 'z061' or '039Y')")
    args = p.parse_args()

    if not args.dir.exists():
        raise SystemExit(f"Error: Directory does not exist: {args.dir}")

    print(f"=== Dataset Inventory ===")
    print(f"Root:   {args.dir.resolve()}")
    print(f"Filter: {args.filter if args.filter else '(none)'}\n")

    # Buckets for categorization
    categories = {
        "Scene & Transform Files (.mrml, .h5)": [],
        "Full-Body CT Volumes (.nii)": [],
        "NRRD Volumes & Masks (.nrrd)": [],
        "NIfTI Volumes & Masks (.nii, .nii.gz)": [],
        "CSV / Metadata (.csv, .json)": []
    }

    # Walk the directory
    for path in args.dir.rglob("*"):
        if not path.is_file():
            continue
            
        # Apply filter if provided
        if args.filter and args.filter.lower() not in str(path).lower():
            continue

        size_str = format_size(path.stat().st_size)
        suffix = path.suffix.lower()
        if path.name.endswith(".nii.gz"):
            suffix = ".nii.gz"

        # Categorize
        if suffix in (".mrml", ".h5"):
            categories["Scene & Transform Files (.mrml, .h5)"].append((path, size_str))
        elif suffix == ".nrrd":
            categories["NRRD Volumes & Masks (.nrrd)"].append((path, size_str))
        elif suffix in (".nii", ".nii.gz"):
            # Guess if it's full-body based on filename
            if "Body" in path.name or "body" in path.name:
                categories["Full-Body CT Volumes (.nii)"].append((path, size_str))
            else:
                categories["NIfTI Volumes & Masks (.nii, .nii.gz)"].append((path, size_str))
        elif suffix in (".csv", ".json"):
            categories["CSV / Metadata (.csv, .json)"].append((path, size_str))

    # Print the report
    for cat_name, files in categories.items():
        if not files:
            continue
        
        print(f"--- {cat_name} ---")
        for file_path, size in sorted(files):
            # Print absolute paths so they can be copy-pasted to WSL (/mnt/d/...)
            print(f"  [{size:>8}]  {file_path}")
        print()

    print("=== End of Inventory ===")

if __name__ == "__main__":
    raise SystemExit(main())