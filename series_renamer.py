#!/usr/bin/env python3
"""
series_renamer.py
------------------------
Nur core logic: Startname parsen, Videosammeln, Vorschau der Namen.
Noch keine tatsächliche Umbenennung.
"""

import os
import re
from pathlib import Path


VIDEO_EXTENSIONS = {".mkv", ".mp4", ".avi", ".m4v", ".ts", ".mov", ".wmv", ".flv"}


def parse_start_name(text: str) -> tuple[str, str, int, int]:
    """
    Erlaubt z.B.: 'Dr. House (2004) S01E01'
    """
    text = text.strip()
    match = re.match(
        r"^(.+?)\s*\((\d{4})\)\s*[Ss](\d{1,2})[Ee](\d{1,3})\s*$",
        text,
    )
    if not match:
        raise ValueError("Format: Show Name (Year) S01E01")
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


def main():
    directory = input("Ordner mit Episoden: ").strip()
    start_name = input("Startname (z. B. Dr. House (2004) S01E01): ").strip()

    show_name, year, season, start_ep = parse_start_name(start_name)
    files = collect_video_files(directory)
    pairs = build_rename_pairs(files, show_name, year, season, start_ep)

    print("\nVorschau:")
    for old, new in pairs:
        print(f"  {old.name}")
        print(f"    → {new.name}\n")


if __name__ == "__main__":
    main()