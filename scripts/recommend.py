#!/usr/bin/env python3
"""
Get 5 song recommendations by song name.
Usage:
  python scripts/recommend.py "Song Title" [--artist "Artist Name"] [--index-dir PATH]
  python scripts/recommend.py   # interactive: prompts for song name
"""
import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import DEFAULT_INDEX_DIR, TOP_K
from src.index import load_index
from src.recommend import recommend, format_recommendations


def main():
    parser = argparse.ArgumentParser(description="Get song recommendations by song name.")
    parser.add_argument(
        "song_name",
        nargs="?",
        default=None,
        help="Title of the song (or run without args for interactive mode)",
    )
    parser.add_argument(
        "--artist",
        type=str,
        default=None,
        help="Artist name (optional, helps if multiple songs share a title)",
    )
    parser.add_argument(
        "--index-dir",
        type=Path,
        default=DEFAULT_INDEX_DIR,
        help=f"Path to index (default: {DEFAULT_INDEX_DIR})",
    )
    args = parser.parse_args()

    if not args.index_dir.exists():
        print(f"Index not found at {args.index_dir}. Run scripts/build_index_from_summary.py first.")
        sys.exit(1)

    scaler, nn, vectors, metadata = load_index(args.index_dir)

    song_name = args.song_name
    if not song_name or not song_name.strip():
        print("Enter a song name (must be a song from the catalogue):")
        song_name = input().strip()
        if not song_name:
            print("No song name provided.")
            sys.exit(1)

    recs, err = recommend(
        scaler, nn, vectors, metadata,
        song_name=song_name,
        artist_name=args.artist,
        top_k=TOP_K,
    )

    if err:
        print(err)
        sys.exit(1)

    print(format_recommendations(recs))


if __name__ == "__main__":
    main()
