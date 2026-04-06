#!/usr/bin/env python3
"""
series_renamer.py
------------------------
Core logic + real file renaming + basic CLI interface.
"""

import os
import re
import sys
import argparse
from pathlib import Path


VIDEO_EXTENSIONS = {".mkv", ".mp4", ".avi", ".m4v", ".ts", ".mov", ".wmv", ".flv"}


def parse_start_name(text: str) -> tuple[str, str, int, int]:
    """
    Parse a user supplied start name such as 'Dr. House (2004) S01E01'.

    Returns (show_name, year, season, start_episode).
    Raises ValueError with a descriptive message on bad input.
    """
    text = text.strip()
    match = re.match(
        r"^(.+?)\s*\((\d{4})\)\s*[Ss](\d{1,2})[Ee](\d{1,3})\s*$",
        text,
    )
    if not match:
        raise ValueError(
            "Unrecognized format.\n"
            "Expected:  Show Name (Year) S01E01\n"
            "Example:   Dr. House (2004) S02E05"
        )
    return (
        match.group(1).strip(),
        match.group(2),
        int(match.group(3)),
        int(match.group(4)),
    )


def _natural_sort_key(path: Path) -> list:
    return [
        int(part) if part.isdigit() else part.lower()
        for part in re.split(r"(\d+)", path.name)
    ]


def collect_video_files(directory: str) -> list[Path]:
    """Return video files in *directory*, sorted in natural order."""
    files = [
        p
        for p in Path(directory).iterdir()
        if p.is_file() and p.suffix.lower() in VIDEO_EXTENSIONS
    ]
    files.sort(key=_natural_sort_key)
    return files


def build_rename_pairs(
    files: list[Path],
    show_name: str,
    year: str,
    season: int,
    start_episode: int,
) -> list[tuple[Path, Path]]:
    """Return (old_path, new_path) pairs without touching the filesystem."""
    pairs = []
    episode = start_episode
    for file in files:
        new_name = (
            f"{show_name} ({year}) "
            f"S{season:02d}E{episode:02d}{file.suffix.lower()}"
        )
        pairs.append((file, file.parent / new_name))
        episode += 1
    return pairs

def rename_files(pairs: list[tuple[Path, Path]]) -> tuple[int, list[str]]:
    """
    Execute renames. Returns (success_count, error_messages).
    """
    success = 0
    errors = []
    for old, new in pairs:
        try:
            old.rename(new)
            success += 1
        except OSError as exc:
            errors.append(f"{old.name}  ->  {exc}")
    return success, errors


# ---------------------------------------------------------------------------
# CLI interface
# ---------------------------------------------------------------------------


def run_cli(directory: str, start_name: str, dry_run: bool = False) -> None:
    try:
        show_name, year, season, start_ep = parse_start_name(start_name)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    files = collect_video_files(directory)
    if not files:
        print("No video files found in the specified directory.")
        sys.exit(0)

    pairs = build_rename_pairs(files, show_name, year, season, start_ep)

    print(f"{'DRY RUN - ' if dry_run else ''}Renaming {len(pairs)} file(s):\n")
    for old, new in pairs:
        print(f"  {old.name}")
        print(f"    -> {new.name}\n")

    if dry_run:
        print("Dry run complete. No files were changed.")
        return

    confirm = input("Proceed? [y/N] ").strip().lower()
    if confirm != "y":
        print("Aborted.")
        sys.exit(0)

    success, errors = rename_files(pairs)
    print(f"\n{success} file(s) renamed successfully.")
    if errors:
        print(f"\n{len(errors)} error(s):")
        for err in errors:
            print(f"  {err}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Batch-rename TV episode files into a structured format."
    )
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Run in command-line mode (no GUI).",
    )
    parser.add_argument(
        "--dir",
        metavar="PATH",
        help="Directory containing the episode files.",
    )
    parser.add_argument(
        "--start",
        metavar="NAME",
        help='Start name, e.g. "Dr. House (2004) S01E01".',
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without renaming anything (CLI mode only).",
    )
    args = parser.parse_args()

    if args.cli:
        if not args.dir or not args.start:
            parser.error("--cli requires both --dir and --start")
        run_cli(args.dir, args.start, dry_run=args.dry_run)
    else:
        directory = input("Ordner mit Episoden: ").strip()
        start_name = input(
            "Startname (z. B. Dr. House (2004) S01E01): "
        ).strip()
        show_name, year, season, start_ep = parse_start_name(start_name)
        files = collect_video_files(directory)
        pairs = build_rename_pairs(files, show_name, year, season, start_ep)

        print("\nVorschau:")
        for old, new in pairs:
            print(f"  {old.name}")
            print(f"    → {new.name}\n")

        confirm = input("Renamen? [y/N] ").strip().lower()
        if confirm == "y":
            success, errors = rename_files(pairs)
            print(f"{success} file(s) renamed.")
            if errors:
                print("Errors:", *errors, sep="\n  ")



if __name__ == "__main__":
    main()