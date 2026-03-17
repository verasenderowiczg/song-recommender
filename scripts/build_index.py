#!/usr/bin/env python3
"""
Build the recommendation index from MSD data.
Usage:
  python scripts/build_index.py [--data-dir PATH] [--index-dir PATH]
"""
import argparse
import sys
from pathlib import Path

# Add project root so we can import src and config
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import DEFAULT_DATA_DIR, DEFAULT_INDEX_DIR, FEATURE_COLUMNS, TOP_K
from src.data import load_msd_dataframe
from src.index import build_index, save_index


def main():
    parser = argparse.ArgumentParser(description="Build song recommendation index from MSD HDF5 data.")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DEFAULT_DATA_DIR,
        help=f"Path to directory containing .h5 files (default: {DEFAULT_DATA_DIR})",
    )
    parser.add_argument(
        "--index-dir",
        type=Path,
        default=DEFAULT_INDEX_DIR,
        help=f"Path to save index (default: {DEFAULT_INDEX_DIR})",
    )
    args = parser.parse_args()

    print("Loading MSD data...")
    df = load_msd_dataframe(args.data_dir, feature_columns=FEATURE_COLUMNS)
    print(f"Loaded {len(df)} tracks.")

    print("Building index (scale + nearest neighbours)...")
    scaler, nn, vectors, metadata = build_index(
        df,
        feature_columns=FEATURE_COLUMNS,
        n_neighbors=TOP_K + 1,
    )
    print(f"Index built. Saving to {args.index_dir}...")
    save_index(scaler, nn, vectors, metadata, args.index_dir)
    print("Done.")


if __name__ == "__main__":
    main()
