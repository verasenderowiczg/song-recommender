# Song recommender (Million Song Dataset)

A **content-based music recommender** that suggests 5 similar songs given a track from the catalogue. It uses the [Million Song Dataset](http://labrosa.ee.columbia.edu/millionsong/) (MSD): each song is represented by audio features (tempo, key, energy, loudness, etc.), and recommendations are the nearest neighbours in that feature space. No vector database or API keys required—everything runs locally.

---

## What you need

- **Python 3.8+**
- **~2 GB free disk space** (for the 1% MSD subset and the built index)
- **A few minutes** to download the data and build the index (one-time)

---

## Step 1: Clone the repo

```bash
git clone https://github.com/verasenderowiczg/song-recommender.git
cd song-recommender
```

(Replace the URL with your fork or the correct repo if different.)

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

You need: `tables` (PyTables, for reading MSD HDF5 files), `pandas`, `numpy`, `scikit-learn`, `joblib`.

---

## Step 4: Get the Million Song Dataset

The recommender needs the **1% subset** of the Million Song Dataset (~10,000 tracks, ~1.8 GB compressed).

1. **Download** the subset:
   - Direct link: [Million Song Subset](http://labrosa.ee.columbia.edu/~dpwe/tmp/millionsongsubset.tar.gz)  
   - Or from the official page: [Getting the dataset → Subset](http://labrosa.ee.columbia.edu/millionsong/pages/getting-dataset#subset)

2. **Extract** the archive. You will get a folder (often named `MillionSongSubset`) that contains a `data` directory. Inside `data`, the `.h5` files are organised in subfolders (e.g. `A/B/C/TRXXXXX.h5`).

3. **Place the data** so the project can find it. Either:
   - **Option A:** Put the **contents** of that `data` folder (all the subfolders with `.h5` files) directly inside the repo’s `data/` folder:
     ```text
     song-recommender/
     └── data/
         ├── A/
         ├── B/
         └── ...   (all .h5 files somewhere under here)
     ```
   - **Option B:** Keep the subset anywhere you like (e.g. `~/Downloads/MillionSongSubset/data`) and pass that path in the next step.

The repo’s `data/` folder is in `.gitignore`—the dataset is not committed to git.

---

## Step 5: Build the index

This step reads all `.h5` files, extracts audio features, scales them, and builds a nearest-neighbour index. Run it **once** after you have the data.

**If you put the data in the repo’s `data/` folder:**

```bash
python scripts/build_index.py
```

**If you put the data somewhere else:**

```bash
python scripts/build_index.py --data-dir /path/to/your/msd/data --index-dir index
```

- `--data-dir`: path to the folder that contains the `.h5` files (or their parent subfolders).
- `--index-dir`: where to save the index (default: `index/` in the repo).

The script prints how many tracks were loaded and writes the index under `index/` (or your chosen path). That folder is gitignored—the index is not committed.

---

## Step 6: Get recommendations

The query song **must** be one of the tracks that were loaded into the index (i.e. a song from the MSD subset). You give its **title** (and optionally the **artist** if the title appears more than once).

**By song title:**

```bash
python scripts/recommend.py "Never Gonna Give You Up"
```

**By title and artist:**

```bash
python scripts/recommend.py "Shape of You" --artist "Ed Sheeran"
```

**Interactive mode** (script asks you for the song name):

```bash
python scripts/recommend.py
```

If the song is not in the index, the script will tell you to pick another.

**Example output:**

```text
Here are your 5 recommendations:

  1. "Song A" — Artist A (genre)
  2. "Song B" — Artist B
  3. "Song C" — Artist C (genre)
  4. "Song D" — Artist D
  5. "Song E" — Artist E
```

---

## Project structure

```text
song-recommender/
├── config/
│   └── settings.py          # Paths, feature list, TOP_K
├── src/
│   ├── data/                # Load MSD from .h5 (PyTables)
│   ├── index/               # Build index (scaler + nearest neighbours), save/load
│   └── recommend/           # Query by song name, format output
├── scripts/
│   ├── build_index.py       # Build index from MSD data
│   └── recommend.py         # Get 5 recommendations by song name
├── data/                    # You put MSD .h5 files here (gitignored)
├── index/                   # Built index (gitignored)
├── requirements.txt
└── README.md
```

---

## Data source and licence

- **Dataset:** [Million Song Dataset](http://labrosa.ee.columbia.edu/millionsong/) (LabROSA, Columbia University / The Echo Nest).  
- **HDF5 schema:** The MSD uses a PyTables-style layout; reading is compatible with the [MSongsDB](https://github.com/tbertinmahieux/MSongsDB) code and documentation.

Licence terms for the dataset and MSongsDB are on their respective sites. This project’s code is separate; you can use it under the licence you prefer for your own repo.
