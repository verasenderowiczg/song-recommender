"""
Load Million Song Dataset from HDF5 files (PyTables format).
Walks a data directory for .h5 files and builds a single DataFrame.
"""
from pathlib import Path
from typing import List, Optional

import pandas as pd

try:
    import tables
except ImportError:
    tables = None  # type: ignore


def _get_str(val) -> str:
    """Decode bytes to str if needed."""
    if val is None:
        return ""
    if isinstance(val, bytes):
        return val.decode("utf-8", errors="replace").strip()
    return str(val).strip()


def _read_one_h5(path: Path) -> Optional[dict]:
    """Read a single MSD HDF5 file (one track). Returns dict or None on error (caller may catch to get first error)."""
    if tables is None:
        raise ImportError("PyTables is required to read MSD HDF5 files. Install with: pip install tables")
    return _read_one_h5_impl(path)


def _read_one_h5_impl(path: Path) -> dict:
    """Read one HDF5 file; raises on error."""
    with tables.open_file(str(path), mode="r") as h5:
        if not hasattr(h5.root, "metadata") or not hasattr(h5.root, "analysis"):
            raise ValueError(f"HDF5 file has no 'metadata' or 'analysis' group (is this MSD format?). Root keys: {list(h5.root._v_children.keys())}")
        meta = h5.root.metadata.songs
        anal = h5.root.analysis.songs
        if meta.nrows == 0 or anal.nrows == 0:
            raise ValueError(f"HDF5 file has no rows in metadata.songs or analysis.songs")

        # PyTables: access columns by attribute (e.g. table.cols.track_id[0])
        def col(table, name, default=None):
            if hasattr(table.cols, name):
                return getattr(table.cols, name)[0]
            return default

        track_id = _get_str(col(anal, "track_id") or col(meta, "track_id"))
        out = {
            "track_id": track_id or path.stem,
            "title": _get_str(col(meta, "title")),
            "artist_name": _get_str(col(meta, "artist_name")),
            "tempo": float(col(anal, "tempo") or 0),
            "key": int(col(anal, "key") or 0),
            "mode": int(col(anal, "mode") or 0),
            "loudness": float(col(anal, "loudness") or 0),
            "duration": float(col(anal, "duration") or 0),
            "energy": float(col(anal, "energy") or 0),
            "danceability": float(col(anal, "danceability") or 0),
        }

        if hasattr(h5.root, "musicbrainz") and hasattr(h5.root.musicbrainz, "songs"):
            mb = h5.root.musicbrainz.songs
            if mb.nrows > 0 and hasattr(mb.cols, "year"):
                out["year"] = int(mb.cols.year[0] or 0)
            else:
                out["year"] = 0
        else:
            out["year"] = 0

        # Genre proxy: first artist term if available
        if hasattr(h5.root.metadata, "artist_terms") and h5.root.metadata.artist_terms.shape[0] > 0:
            try:
                first_term = h5.root.metadata.artist_terms[0]
                out["genre"] = _get_str(first_term) if first_term is not None else ""
            except Exception:
                out["genre"] = ""
        else:
            out["genre"] = ""

        return out


def _find_h5_files(data_dir: Path) -> List[Path]:
    """Recursively find all .h5 files under data_dir."""
    return sorted(data_dir.rglob("*.h5"))


def load_msd_dataframe(
    data_dir: Path,
    feature_columns: Optional[List[str]] = None,
    drop_na_features: bool = True,
) -> pd.DataFrame:
    """
    Load MSD from a directory of HDF5 files into a DataFrame.

    Args:
        data_dir: Path to folder containing .h5 files (e.g. MillionSongSubset/data).
        feature_columns: List of numeric columns to keep for the index; None = use all numeric.
        drop_na_features: If True, drop rows where any feature is NaN or invalid.

    Returns:
        DataFrame with columns: track_id, title, artist_name, genre, year, plus feature columns.
    """
    data_dir = Path(data_dir)
    if not data_dir.is_dir():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")

    files = _find_h5_files(data_dir)
    if not files:
        raise FileNotFoundError(f"No .h5 files found under {data_dir}")

    rows = []
    first_error = None
    for path in files:
        try:
            row = _read_one_h5(path)
            if row is not None:
                rows.append(row)
        except Exception as e:
            if first_error is None:
                first_error = (path, e)
            continue

    if not rows:
        if first_error is not None:
            path, e = first_error
            raise RuntimeError(
                f"No valid tracks could be read from the HDF5 files. "
                f"First error when reading {path}: {e}"
            ) from e
        raise ValueError("No valid tracks could be read from the HDF5 files.")

    df = pd.DataFrame(rows)

    default_features = ["tempo", "key", "mode", "loudness", "duration", "energy", "danceability"]
    feats = feature_columns or default_features
    available = [c for c in feats if c in df.columns]
    if not available:
        raise ValueError(f"None of the feature columns {feats} found in data. Available: {list(df.columns)}")

    if drop_na_features:
        df = df.dropna(subset=available)
        df = df[df["duration"] > 0]  # drop invalid duration

    return df.reset_index(drop=True)
