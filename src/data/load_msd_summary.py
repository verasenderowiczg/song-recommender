"""
Load the MSD summary file (msd_summary_file.h5) and optionally filter by artists.

This file is ~300 MB and contains metadata + scalar audio features for all 1M songs.
Use it to build a custom subset (e.g. by artist) without downloading the full 280 GB.
"""
import re
from pathlib import Path
from typing import List, Optional, Union

import pandas as pd

try:
    import tables
except ImportError:
    tables = None  # type: ignore


def _get_str(val) -> str:
    if val is None:
        return ""
    if isinstance(val, bytes):
        return val.decode("utf-8", errors="replace").strip()
    return str(val).strip()


def _decode_str_col(arr) -> List[str]:
    """Decode a byte or string column to list of str."""
    out = []
    for v in arr:
        out.append(_get_str(v))
    return out


def load_summary_dataframe(
    summary_path: Union[Path, str],
    artists: Optional[List[str]] = None,
    artists_file: Optional[Union[Path, str]] = None,
    feature_columns: Optional[List[str]] = None,
    drop_na_features: bool = True,
) -> pd.DataFrame:
    """
    Load the MSD summary HDF5 and return a DataFrame (optionally filtered by artists).

    The summary file has /metadata/songs and /analysis/songs with the same row order.
    It contains scalar audio features (tempo, key, loudness, etc.) for all ~1M tracks;
    no need to download the full 280 GB of per-track files.

    Args:
        summary_path: Path to msd_summary_file.h5.
        artists: Optional list of artist names (case-insensitive substring match).
                 If given, only rows whose artist_name contains any of these are kept.
        artists_file: Optional path to a text file with one artist name per line.
                      Ignored if artists is also given.
        feature_columns: Columns to keep for the index; None = default set.
        drop_na_features: If True, drop rows with NaN or invalid features.

    Returns:
        DataFrame with track_id, title, artist_name, genre (empty), year, and feature columns.
    """
    if tables is None:
        raise ImportError("PyTables is required. Install with: pip install tables")

    summary_path = Path(summary_path)
    if not summary_path.is_file():
        raise FileNotFoundError(f"Summary file not found: {summary_path}")

    # Resolve artist filter
    artist_list: Optional[List[str]] = None
    if artists is not None and len(artists) > 0:
        artist_list = [a.strip().lower() for a in artists if a and str(a).strip()]
    elif artists_file is not None:
        ap = Path(artists_file)
        if not ap.is_file():
            raise FileNotFoundError(f"Artists file not found: {ap}")
        artist_list = [
            line.strip().lower()
            for line in ap.read_text(encoding="utf-8", errors="replace").splitlines()
            if line.strip()
        ]

    with tables.open_file(str(summary_path), mode="r") as h5:
        if not hasattr(h5.root, "metadata") or not hasattr(h5.root, "analysis"):
            raise ValueError(
                "Summary file has no 'metadata' or 'analysis' group. "
                f"Root: {list(h5.root._v_children.keys())}"
            )
        meta = h5.root.metadata.songs
        anal = h5.root.analysis.songs
        n = meta.nrows
        if anal.nrows != n:
            raise ValueError(
                f"Row count mismatch: metadata.songs={n}, analysis.songs={anal.nrows}"
            )

        # Read columns we need (same row order in both tables)
        def read_col(table, name, dtype=str):
            if not hasattr(table.cols, name):
                return None
            col = getattr(table.cols, name)
            if dtype == str:
                return _decode_str_col(col[:])
            return col[:]

        # Metadata
        title = read_col(meta, "title") or [""] * n
        artist_name = read_col(meta, "artist_name") or [""] * n
        # Analysis
        track_id = read_col(anal, "track_id") or read_col(meta, "track_id")
        if track_id is None:
            track_id = [f"TR{i:06d}" for i in range(n)]
        tempo = read_col(anal, "tempo", float) if hasattr(anal.cols, "tempo") else [0.0] * n
        key = read_col(anal, "key", int) if hasattr(anal.cols, "key") else [0] * n
        mode = read_col(anal, "mode", int) if hasattr(anal.cols, "mode") else [0] * n
        loudness = read_col(anal, "loudness", float) if hasattr(anal.cols, "loudness") else [0.0] * n
        duration = read_col(anal, "duration", float) if hasattr(anal.cols, "duration") else [0.0] * n
        energy = read_col(anal, "energy", float) if hasattr(anal.cols, "energy") else [0.0] * n
        danceability = (
            read_col(anal, "danceability", float)
            if hasattr(anal.cols, "danceability")
            else [0.0] * n
        )

        # Year from musicbrainz if present
        if hasattr(h5.root, "musicbrainz") and hasattr(h5.root.musicbrainz, "songs"):
            mb = h5.root.musicbrainz.songs
            if mb.nrows == n and hasattr(mb.cols, "year"):
                year = mb.cols.year[:]
            else:
                year = [0] * n
        else:
            year = [0] * n

    df = pd.DataFrame({
        "track_id": track_id,
        "title": title,
        "artist_name": artist_name,
        "genre": "",  # Summary file has no artist_terms
        "year": year,
        "tempo": _to_float(tempo),
        "key": _to_int(key),
        "mode": _to_int(mode),
        "loudness": _to_float(loudness),
        "duration": _to_float(duration),
        "energy": _to_float(energy),
        "danceability": _to_float(danceability),
    })

    # Filter by artists (case-insensitive substring match)
    if artist_list:
        an = df["artist_name"].astype(str).str.lower()
        mask = an.str.contains("|".join(re.escape(a) for a in artist_list), regex=True, na=False)
        df = df.loc[mask].reset_index(drop=True)
        if df.empty:
            raise ValueError(
                "No rows left after filtering by artists. "
                "Check spelling and that names match the dataset."
            )

    default_features = ["tempo", "key", "mode", "loudness", "duration", "energy", "danceability"]
    feats = feature_columns or default_features
    available = [c for c in feats if c in df.columns]
    if not available:
        raise ValueError(
            f"None of the feature columns {feats} found. Available: {list(df.columns)}"
        )

    if drop_na_features:
        df = df.dropna(subset=available)
        df = df[df["duration"] > 0]

    return df.reset_index(drop=True)


def _to_float(arr) -> List[float]:
    out = []
    for v in arr:
        try:
            out.append(float(v) if v is not None else 0.0)
        except (TypeError, ValueError):
            out.append(0.0)
    return out


def _to_int(arr) -> List[int]:
    out = []
    for v in arr:
        try:
            out.append(int(v) if v is not None else 0)
        except (TypeError, ValueError):
            out.append(0)
    return out
