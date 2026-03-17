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

### 4.1 Download

- **Direct link:** [millionsongsubset.tar.gz](http://labrosa.ee.columbia.edu/~dpwe/tmp/millionsongsubset.tar.gz) (~1.8 GB)  
- Or open the [official “Getting the dataset” page](http://labrosa.ee.columbia.edu/millionsong/pages/getting-dataset#subset) and use the “Million Song Subset” link there.

If the direct link fails (e.g. 500 error or timeout), try again later—the LabROSA server can be flaky. You can also search for “Million Song Dataset subset” for mirrors (e.g. Academic Torrents) if needed.

From the terminal you can download with (optional):

```bash
curl -L -o millionsongsubset.tar.gz "http://labrosa.ee.columbia.edu/~dpwe/tmp/millionsongsubset.tar.gz"
```

(Or use your browser and save the file.)

### 4.2 Extract

From the folder where you saved the `.tar.gz` file:

```bash
tar -xzf millionsongsubset.tar.gz
```

You should get a folder named **`MillionSongSubset`**. The `.h5` files can be in either of these layouts (depending on the subset version):

- **Layout 1:** `MillionSongSubset/A/`, `MillionSongSubset/B/`, … (letter folders directly inside `MillionSongSubset`, with `.h5` files in subfolders like `A/R/R/TRXXXXX.h5`).
- **Layout 2:** `MillionSongSubset/data/A/`, `MillionSongSubset/data/B/`, … (letter folders inside a `data` subfolder).

The folder the project needs is the one that **directly contains** the letter folders (`A`, `B`, `C`, …): that’s either **`MillionSongSubset`** (layout 1) or **`MillionSongSubset/data`** (layout 2). You may also see `MillionSongSubset/AdditionalFiles/`; we don’t use it.

**Windows:** If `tar` isn’t available, use 7-Zip or another tool to extract the `.tar.gz`, or use Git Bash which includes `tar`.

### 4.3 Place the data so the project can find it

Pick one of these:

- **Option A — use the repo’s `data/` folder (simplest for Step 5)**  
  Move the **letter folders** (`A`, `B`, `C`, …) into the repo’s `data/` folder. Those folders are either directly inside `MillionSongSubset` (layout 1) or inside `MillionSongSubset/data/` (layout 2). Result should look like:

  ```text
  song-recommender/
  └── data/
      ├── A/
      ├── B/
      ├── C/
      └── ...   (more letter folders, each with .h5 files inside)
  ```

  So you do **not** put the whole `MillionSongSubset` folder inside `data/`—only the letter folders (and their contents).

- **Option B — keep the subset where it is**  
  Leave `MillionSongSubset` where it is (e.g. in the repo or in `~/Downloads`). In Step 5 you’ll pass the path that **directly contains** the letter folders:
  - If you have `MillionSongSubset/A/`, `MillionSongSubset/B/`, … use: `--data-dir MillionSongSubset` (or the full path, e.g. `--data-dir ~/Downloads/MillionSongSubset`).
  - If you have `MillionSongSubset/data/A/`, … use: `--data-dir MillionSongSubset/data`.

- **Option B variant — you put the whole `MillionSongSubset` inside repo’s `data/`**  
  If you have `song-recommender/data/MillionSongSubset/A/...`, use:
  ```bash
  python scripts/build_index.py --data-dir data/MillionSongSubset
  ```
  If you have `song-recommender/data/MillionSongSubset/data/A/...`, use:
  ```bash
  python scripts/build_index.py --data-dir data/MillionSongSubset/data
  ```

The repo’s `data/` folder is in `.gitignore`—the dataset is not committed to git.

### 4.4 Verify before Step 5

Check that `.h5` files are under the path you’ll use as `--data-dir`:

- **If you used Option A** (letter folders in repo’s `data/`):
  ```bash
  find data -name "*.h5" | head -5
  ```
  You should see paths like `data/A/R/R/TRXXXXX.h5` (or similar).

- **If you used Option B** with the subset in the repo (e.g. `MillionSongSubset/A/...`):
  ```bash
  find MillionSongSubset -name "*.h5" | head -5
  ```
  You should see paths like `MillionSongSubset/A/R/R/TRXXXXX.h5`.

If you see `.h5` files, you’re ready for Step 5. If not, the path is wrong—make sure `--data-dir` points at the folder that **directly contains** the letter folders (`A`, `B`, …).

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
