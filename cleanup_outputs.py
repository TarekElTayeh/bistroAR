#!/usr/bin/env python3
"""Utility to remove generated output files."""

import argparse
from pathlib import Path
from typing import Iterable


def _remove_files(paths: Iterable[str]) -> None:
    for name in paths:
        p = Path(name)
        if p.exists():
            p.unlink()
            print(f"Removed {p}")
        else:
            print(f"Skipping missing file {p}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Delete generated output files")
    parser.add_argument("--csv", nargs="*", default=[], help="CSV files to remove")
    parser.add_argument("--json", nargs="*", default=[], help="JSON files to remove")
    parser.add_argument("--excel", nargs="*", default=[], help="Excel files to remove")
    parser.add_argument("--pdf", nargs="*", default=[], help="PDF files to remove")
    args = parser.parse_args()

    if not any([args.csv, args.json, args.excel, args.pdf]):
        print("No files specified for cleanup.")
        return

    _remove_files(args.csv)
    _remove_files(args.json)
    _remove_files(args.excel)
    _remove_files(args.pdf)


if __name__ == "__main__":
    main()
