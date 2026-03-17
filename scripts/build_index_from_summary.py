#!/usr/bin/env python3
"""
Build the recommendation index from the MSD summary file (~300 MB), optionally filtered by artists.

This lets you build a custom subset (e.g. only artists you care about) without downloading
the full 280 GB of per-track HDF5 files.

Usage:
  # Download the summary file first (see README), then:

  # All 1M songs (large index):
  python scripts/build_index_from_summary.py --summary path/to/msd_summary_file.h5

  # Only artists whose name contains "Beatles" or "Radiohead":
  python scripts/build_index_from_summary.py --summary path/to/msd_summary_file.h5 --artists "Beatles" "Radiohead"

  # Artists from a text file (one name per line):
  python scripts/build_index_from_summary.py --summary path/to/msd_summary_file.h5 --artists-file artists.txt
"""
import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import DEFAULT_INDEX_DIR, FEATURE_COLUMNS, TOP_K
from src.data import load_summary_dataframe
from src.index import build_index, save_index


def main():
    parser = argparse.ArgumentParser(
        description="Build recommendation index from MSD summary file (no 280 GB download)."
    )
    parser.add_argument(
        "--summary",
        type=Path,
        required=True,
        help="Path to msd_summary_file.h5 (~300 MB, from MSD Additional Files).",
    )
    parser.add_argument(
        "--artists",
        nargs="*",
        default=None,
        help="Artist names (substring match). Only these artists are included. Example: --artists Beatles Radiohead",
    )
    parser.add_argument(
        "--artists-file",
        type=Path,
        default=None,
        help="Path to a text file with one artist name per line (alternative to --artists).",
    )
    parser.add_argument(
        "--index-dir",
        type=Path,
        default=DEFAULT_INDEX_DIR,
        help=f"Where to save the index (default: {DEFAULT_INDEX_DIR})",
    )
    args = parser.parse_args()

    artists = args.artists if args.artists else None
    if artists is not None and len(artists) == 0:
        artists = None

    df = load_summary_dataframe(
        args.summary,
        artists=artists,
        artists_file=args.artists_file,
        feature_columns=FEATURE_COLUMNS,
        drop_na_features=True,
    )
    print(f"Loaded {len(df)} tracks from summary (after filtering).")

    scaler, nn, X_scaled, metadata = build_index(
        df,
        FEATURE_COLUMNS,
        n_neighbors=TOP_K + 1,
    )
    save_index(scaler, nn, X_scaled, metadata, args.index_dir)
    print(f"Index saved to {args.index_dir}")


if __name__ == "__main__":
    main()
