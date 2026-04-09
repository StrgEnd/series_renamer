#!/usr/bin/env python3
"""
series_renamer.py
------------------------
Core logic + CLI + GUI with styling, Treeview table and conflict highlighting.
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
    # ---- Palette ----------------------------------------------------------
    BG      = "#f4f4f2"
    SURFACE = "#ffffff"
    BORDER  = "#ddddd8"
    TEXT    = "#1c1c1c"
    MUTED   = "#6b6b6b"
    ACCENT  = "#2563eb"
    DANGER  = "#dc2626"
    SUCCESS = "#16a34a"
    ROW_ALT = "#f9f9f7"

    def __init__(self):
        super().__init__()
        self.title("Series Renamer")
        self.minsize(820, 560)
        self._pairs: list[tuple[Path, Path]] = []
        self._build_styles()
        self._build_ui()
    
    # ---- Styles -----------------------------------------------------------
    def _build_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure("TFrame", background=self.BG)
        style.configure("Surface.TFrame", background=self.SURFACE)

        style.configure(
            "TLabel",
            background=self.BG,
            foreground=self.TEXT,
            font=("Segoe UI", 10),
        )
        style.configure(
            "Title.TLabel",
            background=self.BG,
            foreground=self.TEXT,
            font=("Segoe UI", 16, "bold"),
        )
        style.configure(
            "Caption.TLabel",
            background=self.BG,
            foreground=self.MUTED,
            font=("Segoe UI", 9),
        )
        style.configure(
            "Status.TLabel",
            background=self.BG,
            foreground=self.MUTED,
            font=("Segoe UI", 9),
        )
        style.configure(
            "TEntry",
            fieldbackground=self.SURFACE,
            foreground=self.TEXT,
            bordercolor=self.BORDER,
            insertcolor=self.TEXT,
            font=("Segoe UI", 10),
            padding=(6, 4),
        )
        style.configure(
            "TButton",
            background=self.SURFACE,
            foreground=self.TEXT,
            font=("Segoe UI", 10),
            bordercolor=self.BORDER,
            focusthickness=0,
            padding=(10, 5),
        )
        style.map(
            "TButton",
            background=[("active", self.BORDER), ("disabled", self.BG)],
            foreground=[("disabled", self.MUTED)],
        )
        style.configure(
            "Primary.TButton",
            background=self.ACCENT,
            foreground="#ffffff",
            font=("Segoe UI", 10, "bold"),
            borderwidth=0,
            padding=(14, 6),
        )
        style.map(
            "Primary.TButton",
            background=[("active", "#1d4ed8"), ("disabled", "#93c5fd")],
            foreground=[("disabled", "#ffffff")],
        )
        style.configure(
            "Treeview",
            background=self.SURFACE,
            foreground=self.TEXT,
            fieldbackground=self.SURFACE,
            rowheight=26,
            font=("Consolas", 9),
            borderwidth=0,
        )
        style.configure(
            "Treeview.Heading",
            background=self.BG,
            foreground=self.MUTED,
            font=("Segoe UI", 9, "bold"),
            borderwidth=0,
            relief="flat",
        )
        style.map(
            "Treeview",
            background=[("selected", "#eff6ff")],
            foreground=[("selected", self.ACCENT)],
        )

    # ---- UI ---------------------------------------------------------------

    def _build_ui(self):
        # Top bar
        top = ttk.Frame(self, padding=(24, 20, 24, 12))
        top.pack(fill="x")
        ttk.Label(top, text="Series Renamer", style="Title.TLabel").pack(
            anchor="w"
        )
        ttk.Label(
            top,
            text="Batch‑rename TV episode files into a structured format.",
            style="Caption.TLabel",
        ).pack(anchor="w", pady=(2, 0))

        # Separator
        sep = tk.Frame(self, height=1, bg=self.BORDER)
        sep.pack(fill="x")

        # Input panel
        panel = ttk.Frame(self, padding=(24, 16, 24, 8))
        panel.pack(fill="x")

        # Directory row
        ttk.Label(panel, text="Source directory").grid(
            row=0, column=0, sticky="w", pady=(0, 4)
        )
        dir_row = ttk.Frame(panel)
        dir_row.grid(row=1, column=0, sticky="ew", pady=(0, 12))
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
            style="Caption.TLabel",
        ).grid(row=2, column=0, sticky="e")

        self.var_start = tk.StringVar(value="Dr. House (2004) S01E01")
        ttk.Entry(panel, textvariable=self.var_start).grid(
            row=3, column=0, sticky="ew"
        )

        # Buttons
        btn_row = ttk.Frame(self, padding=(24, 10, 24, 8))
        btn_row.pack(fill="x")
        ttk.Button(btn_row, text="Preview", command=self._preview).pack(
            side="left"
        )
        self.btn_rename = ttk.Button(
            btn_row,
            text="Rename files",
            style="Primary.TButton",
            command=self._rename,
            state="disabled",
        )
        self.btn_rename.pack(side="left", padx=(10, 0))

        # Separator
        sep2 = tk.Frame(self, height=1, bg=self.BORDER)
        sep2.pack(fill="x")


        # Preview table
        tree_frame = ttk.Frame(self, padding=(24, 12, 24, 0))
        tree_frame.pack(fill="both", expand=True)

        cols = ("before", "after")
        self.tree = ttk.Treeview(
            tree_frame, columns=cols, show="headings", selectmode="none"
        )
        self.tree.heading("before", text="Current filename")
        self.tree.heading("after", text="New filename")
        self.tree.column("before", width=340, anchor="w", stretch=True)
        self.tree.column("after", width=340, anchor="w", stretch=True)
        self.tree.tag_configure("conflict", foreground=self.DANGER)
        self.tree.tag_configure("ok", foreground=self.TEXT)
        self.tree.tag_configure("alt", background=self.ROW_ALT)

        scrollbar = ttk.Scrollbar(
            tree_frame, orient="vertical", command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True)

        # Status bar
        sep3 = tk.Frame(self, height=1, bg=self.BORDER)
        sep3.pack(fill="x")
        self.var_status = tk.StringVar(
            value="Select a directory and enter a start name, then click Preview."
        )
        ttk.Label(
            self,
            textvariable=self.var_status,
            style="Status.TLabel",
            padding=(24, 6),
        ).pack(anchor="w")

    # ---- Handlers ---------------------------------------------------------
    def _browse(self):
        path = filedialog.askdirectory(
            title="Select directory containing episode files"
        )
        if path:
            self.var_dir.set(path)

    def _preview(self):
        self.tree.delete(*self.tree.get_children())
        self.btn_rename.configure(state="disabled")
        self._pairs = []

        directory = self.var_dir.get().strip()
        if not directory or not os.path.isdir(directory):
            messagebox.showerror(
                "Invalid directory",
                "Please select a valid directory.",
            )
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
            self.var_status.set("No video files found in the selected directory.")
            return

        pairs = build_rename_pairs(files, show_name, year, season, start_ep)
        conflicts = 0

        for i, (old, new) in enumerate(pairs):
            has_conflict = new.exists() and new != old
            if has_conflict:
                conflicts += 1
            tag = "conflict" if has_conflict else ("alt" if i % 2 else "ok")
            self.tree.insert(
                "", "end", values=(old.name, new.name), tags=(tag,)
            )

        self._pairs = pairs

        parts = [f"{len(pairs)} file(s) ready to rename."]
        if conflicts:
            parts.append(f"{conflicts} conflict(s) highlighted in red.")
        self.var_status.set("  ".join(parts))
        self.btn_rename.configure(state="normal")

    def _rename(self):
        if not self._pairs:
            return

        conflicts = [
            (o, n) for o, n in self._pairs if n.exists() and n != o
        ]
        if conflicts:
            proceed = messagebox.askyesno(
                "Conflicts detected",
                f"{len(conflicts)} file(s) would be overwritten. Proceed anyway?",
            )
            if not proceed:
                return

        success, errors = rename_files(self._pairs)
        self._pairs = []
        self.btn_rename.configure(state="disabled")
        self.tree.delete(*self.tree.get_children())

        if errors:
            messagebox.showwarning(
                "Partial success",
                f"{success} file(s) renamed.\n\n"
                f"{len(errors)} error(s):\n" + "\n".join(errors),
            )
        else:
            messagebox.showinfo("Done", f"{success} file(s) renamed successfully.")

        self.var_status.set(f"{success} file(s) renamed.")

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Batch rename TV episode files into a structured format."
    )
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Run in command line mode (no GUI).",
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