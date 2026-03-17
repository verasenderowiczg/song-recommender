# Song recommender (Million Song Dataset)

A **content-based music recommender** that suggests 5 similar songs given a track from the catalogue. It uses the [Million Song Dataset](http://labrosa.ee.columbia.edu/millionsong/) (MSD) **summary file** (~300 MB): each song is represented by scalar audio features (tempo, key, energy, loudness, etc.), and recommendations are the nearest neighbours in that feature space. No 280 GB download, no vector database, no API keys—everything runs locally.

---

## What you need

- **Python 3.8+**
- **~500 MB free disk space** (summary file + built index)
- **A few minutes** to download the summary and build the index (one-time)

---

## Step 1: Clone the repo

```bash
git clone https://github.com/verasenderowiczg/song-recommender.git
cd song-recommender
```

(Replace the URL with your fork if different.)

---

## Step 2: Set up a virtual environment (recommended)

```bash
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
```

---

## Step 3: Install dependencies

```bash
pip install -r requirements.txt
```

You need: `tables` (PyTables, for reading the MSD summary HDF5), `pandas`, `numpy`, `scikit-learn`, `joblib`.

---

## Step 4: Get the MSD summary file

The recommender uses the **summary file** of the full Million Song Dataset: one ~300 MB HDF5 file with metadata and scalar audio features for **all ~1 million songs**. You do not need the full 280 GB dataset.

- **URL:** [msd_summary_file.h5](http://millionsongdataset.com/sites/default/files/AdditionalFiles/msd_summary_file.h5) (~300 MB)
- From the [MSD “Getting the dataset”](http://millionsongdataset.com/pages/getting-dataset/) page it’s under “Additional Files” → “Summary file of the whole dataset”.

Download and save it somewhere (e.g. `~/Downloads/msd_summary_file.h5` or `data/msd_summary_file.h5` in the repo). The repo ignores `*.h5`, so it won’t be committed.

---

## Step 5: Build the index

Build the recommendation index from the summary file. Run **once** after you have the file.

**All ~1M songs** (full catalogue):

```bash
python scripts/build_index_from_summary.py --summary /path/to/msd_summary_file.h5
```

Use the actual path where you saved the file (e.g. `--summary ~/Downloads/msd_summary_file.h5`).

**Only certain artists** (smaller, faster index). By name(s):

```bash
python scripts/build_index_from_summary.py --summary /path/to/msd_summary_file.h5 --artists "Beatles" "Radiohead"
```

By text file (one artist name per line):

```bash
python scripts/build_index_from_summary.py --summary /path/to/msd_summary_file.h5 --artists-file artists.txt
```

Artist matching is **case-insensitive substring** (e.g. `beatles` matches “The Beatles”). The index is written to `index/` (or `--index-dir PATH`). That folder is gitignored.

---

## Step 6: Get recommendations

The query song must be one of the tracks in the index. Give its **title** (and optionally **artist** if the title appears more than once).

**By song title:**

```bash
python scripts/recommend.py "Never Gonna Give You Up"
```

**By title and artist:**

```bash
python scripts/recommend.py "Shape of You" --artist "Ed Sheeran"
```

**Interactive mode** (script prompts for the song name):

```bash
python scripts/recommend.py
```

If the song is not in the index, the script will ask you to pick another.

**Example output:**

```text
Here are your 5 recommendations:

  1. "Song A" — Artist A (genre)
  2. "Song B" — Artist B
  ...
```

---

## Export song list for filtering

To let a teammate choose which songs to keep (e.g. for a smaller subset), export the current catalogue to a CSV they can open in Excel or Google Sheets:

```bash
python scripts/export_song_list_for_filtering.py
```

This creates **`song_list_for_filtering.csv`** with columns: **Title**, **Artist**, **Genre**, **Track ID**, and an empty **Include (Y/N)** column. They can filter and mark rows, then you can use that list (e.g. to build an index with `--artists-file` or a derived list).

- `--index-dir PATH` if your index is not in the default `index/` folder.
- `--output PATH` to write the CSV elsewhere (e.g. `--output ~/Desktop/songs_to_filter.csv`).

Run this after building the index (Step 5).

---

## Project structure

```text
song-recommender/
├── config/
│   └── settings.py          # Paths, feature list, TOP_K
├── src/
│   ├── data/                # Load MSD summary HDF5 (PyTables)
│   ├── index/               # Build index (scaler + nearest neighbours), save/load
│   └── recommend/           # Query by song name, format output
├── scripts/
│   ├── build_index_from_summary.py   # Build index from summary file (all 1M or filtered)
│   ├── export_song_list_for_filtering.py   # Export catalogue to CSV for team filtering
│   └── recommend.py         # Get 5 recommendations by song name
├── index/                   # Built index (gitignored)
├── requirements.txt
└── README.md
```

---

## Data source and licence

- **Dataset:** [Million Song Dataset](http://labrosa.ee.columbia.edu/millionsong/) (LabROSA, Columbia University / The Echo Nest).
- **Summary file:** Same HDF5 layout as per-track files for metadata and scalar analysis (tempo, key, loudness, etc.); no segment/beat arrays. See [MSD field list](http://millionsongdataset.com/pages/field-list/) and [MSongsDB](https://github.com/tbertinmahieux/MSongsDB) for schema details.

Licence terms for the dataset are on the MSD site. This project’s code is separate; use it under the licence you prefer for your repo.
