#!/usr/bin/env python3
"""
series_renamer.py
------------------------
Core logic + CLI + basic GUI.
"""

import os
import re
import sys
import argparse
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
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
# GUI interface (basic)
# ---------------------------------------------------------------------------


class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Series Renamer")
        self.minsize(600, 400)
        self._pairs: list[tuple[Path, Path]] = []
        self._build_ui()

    def _build_ui(self):
        # Top bar
        top = ttk.Frame(self, padding=(12, 10, 12, 6))
        top.pack(fill="x")
        ttk.Label(top, text="Series Renamer", font=("Segoe UI", 12, "bold")).pack(
            anchor="w"
        )
        ttk.Label(
            top,
            text="Batch‑rename TV episode files into a structured format.",
        ).pack(anchor="w", pady=(2, 0))

        # Separator
        sep = tk.Frame(self, height=1, bg="#ccc")
        sep.pack(fill="x", pady=(4, 0))

        # Directory row
        panel = ttk.Frame(self, padding=(12, 8, 12, 4))
        panel.pack(fill="x")

        ttk.Label(panel, text="Source directory").grid(
            row=0, column=0, sticky="w", pady=(0, 4)
        )
        dir_row = ttk.Frame(panel)
        dir_row.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        panel.columnconfigure(0, weight=1)

        self.var_dir = tk.StringVar()
        ttk.Entry(dir_row, textvariable=self.var_dir).pack(
            side="left", fill="x", expand=True
        )
        ttk.Button(dir_row, text="Browse...", command=self._browse).pack(
            side="left", padx=(8, 0)
        )

        # Start name row
        ttk.Label(panel, text="Start name").grid(
            row=2, column=0, sticky="w", pady=(0, 4)
        )
        ttk.Label(
            panel,
            text="Format: Show Name (Year) S01E01",
        ).grid(row=2, column=0, sticky="e")

        self.var_start = tk.StringVar(value="Dr. House (2004) S01E01")
        ttk.Entry(panel, textvariable=self.var_start).grid(
            row=3, column=0, sticky="ew"
        )

        # Buttons
        btn_row = ttk.Frame(self, padding=(12, 6, 12, 6))
        btn_row.pack(fill="x")
        ttk.Button(btn_row, text="Preview", command=self._preview).pack(
            side="left"
        )
        self.btn_rename = ttk.Button(
            btn_row,
            text="Rename files",
            state="disabled",
            command=self._rename,
        )
        self.btn_rename.pack(side="left", padx=(10, 0))

        # Separator
        sep2 = tk.Frame(self, height=1, bg="#ccc")
        sep2.pack(fill="x", pady=(4, 0))

        # Output area
        out_frame = ttk.Frame(self, padding=(12, 8, 12, 8))
        out_frame.pack(fill="both", expand=True)
        self.text_out = tk.Text(
            out_frame,
            height=10,
            font=("Consolas", 9),
            wrap="none",
        )
        text_scroll = tk.Scrollbar(
            out_frame, orient="vertical", command=self.text_out.yview
        )
        self.text_out.configure(yscrollcommand=text_scroll.set)
        self.text_out.pack(side="left", fill="both", expand=True)
        text_scroll.pack(side="right", fill="y")

        # Status bar
        status_frame = ttk.Frame(self, padding=(12, 4, 12, 4))
        status_frame.pack(fill="x")
        self.var_status = tk.StringVar(
            value="Enter directory and start name, then click Preview."
        )
        ttk.Label(
            status_frame,
            textvariable=self.var_status,
            foreground="#555",
            font=("Segoe UI", 9),
        ).pack(anchor="w")

    def _browse(self):
        path = filedialog.askdirectory(title="Select directory")
        if path:
            self.var_dir.set(path)

    def _preview(self):
        self.text_out.delete("1.0", "end")
        self._pairs = []
        self.btn_rename.configure(state="disabled")

        directory = self.var_dir.get().strip()
        if not directory or not os.path.isdir(directory):
            messagebox.showerror("Invalid directory", "Please select a valid directory.")
            return

        try:
            show_name, year, season, start_ep = parse_start_name(
                self.var_start.get()
            )
        except ValueError as exc:
            messagebox.showerror("Format error", str(exc))
            return

        files = collect_video_files(directory)
        if not files:
            self.var_status.set("No video files found in selected directory.")
            return

        pairs = build_rename_pairs(files, show_name, year, season, start_ep)
        self._pairs = pairs

        for old, new in pairs:
            self.text_out.insert("end", f"{old.name}\n")
            self.text_out.insert("end", f"  → {new.name}\n\n")

        self.var_status.set(
            f"Preview: {len(pairs)} file(s) ready to rename."
        )
        self.btn_rename.configure(state="normal")

    def _rename(self):
        if not self._pairs:
            return

        success, errors = rename_files(self._pairs)
        self._pairs = []
        self.btn_rename.configure(state="disabled")
        self.text_out.delete("1.0", "end")

        if errors:
            messagebox.showwarning(
                "Partial success",
                f"{success} file(s) renamed.\n\n"
                f"{len(errors)} error(s):\n" + "\n".join(errors),
            )
        else:
            messagebox.showinfo(
                "Done", f"{success} file(s) renamed successfully."
            )

        self.var_status.set(f"{success} file(s) renamed.")

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
        app = Application()
        app.mainloop()


if __name__ == "__main__":
    main()