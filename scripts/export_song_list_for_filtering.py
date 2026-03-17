#!/usr/bin/env python3
"""
Export the current catalogue to a CSV table for filtering (e.g. in Excel or Google Sheets).
Your teammate can add a column or filter by artist/genre to decide which songs to keep.
Usage:
  python scripts/export_song_list_for_filtering.py [--index-dir PATH] [--output PATH]
"""
import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import DEFAULT_INDEX_DIR


def main():
    parser = argparse.ArgumentParser(
        description="Export song list from the index to a CSV for filtering by your team."
    )
    parser.add_argument(
        "--index-dir",
        type=Path,
        default=DEFAULT_INDEX_DIR,
        help=f"Path to the index (default: {DEFAULT_INDEX_DIR})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("song_list_for_filtering.csv"),
        help="Output CSV path (default: song_list_for_filtering.csv in current directory)",
    )
    args = parser.parse_args()

    metadata_path = args.index_dir / "metadata.csv"
    if not metadata_path.exists():
        print(f"Index not found at {args.index_dir}. Run scripts/build_index_from_summary.py first.")
        sys.exit(1)

    import pandas as pd
    df = pd.read_csv(metadata_path)

    # Column order and display names for the filtering table
    col_spec = [
        ("title", "Title"),
        ("artist_name", "Artist"),
        ("genre", "Genre"),
        ("track_id", "Track ID"),
    ]
    cols = [c for c, _ in col_spec if c in df.columns]
    names = [n for c, n in col_spec if c in df.columns]
    out = df[cols].copy()
    out.columns = names
    out["Include (Y/N)"] = ""  # Teammate fills this to mark which rows to keep

    args.output = Path(args.output)
    out.to_csv(args.output, index=False, encoding="utf-8")
    print(f"Exported {len(out)} songs to {args.output}")
    print("Your teammate can open this in Excel or Google Sheets and filter or fill 'Include (Y/N)'.")


if __name__ == "__main__":
    main()
