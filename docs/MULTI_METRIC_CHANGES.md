# Guide: Add Euclidean, Manhattan, and Cosine Recommendations

**Goal:** Change the recommender so it returns results for **all three** distance metrics (euclidean, manhattan, cosine) by default, so you can compare which you like best.

**Idea:** Right now there is a single `NearestNeighbors` model with `metric="euclidean"`. You will:
1. Define a list of metrics (euclidean, manhattan, cosine) in config.
2. At **build** time: create and save **one NN model per metric** (same vectors, different metric).
3. At **query** time: load all models, run KNN for each metric, and print three blocks of recommendations (one per metric).

---

## 1. Config: which metrics to use

**File:** `config/settings.py`

**What to do:** Add a constant list of metrics used everywhere (build + load + recommend).

- **Where:** After `TOP_K = 5`, add a new line, e.g.:
  ```python
  METRICS = ["euclidean", "manhattan", "cosine"]
  ```
- **Why:** Single place to add/remove metrics. Build and recommend scripts should import this.

---

## 2. Build: one NN model per metric

**File:** `src/index/build.py`

**What to do:** Instead of building a single `NearestNeighbors(metric="euclidean")`, build one model per metric and return a **dict** `{ "euclidean": nn_euc, "manhattan": nn_man, "cosine": nn_cos }`.

- **Where (around line 38):**  
  Right now you have something like:
  ```python
  nn = NearestNeighbors(n_neighbors=n_neighbors, metric="euclidean", algorithm="auto")
  nn.fit(X_scaled)
  ```
  Replace that with a loop over the metrics list (import `METRICS` from `config.settings`). For each metric, create `NearestNeighbors(n_neighbors=..., metric=m, algorithm="auto")`, fit it on `X_scaled`, and store it in a dict (e.g. `nn_by_metric[m] = nn`).

- **Return value:** Change the function so it returns `(scaler, nn_by_metric, X_scaled, metadata)` instead of `(scaler, nn, X_scaled, metadata)`. Update the type hint: the second return is now a dict mapping metric name (str) to `NearestNeighbors`.

---

## 3. Store: save and load one file per metric

**File:** `src/index/store.py`

**What to do:** Save/load multiple NN models (one per metric) instead of a single `nn.joblib`.

- **`save_index`**
  - **Signature:** Change the second argument from `nn: NearestNeighbors` to `nn_by_metric` (a dict: metric name → `NearestNeighbors`).
  - **Where (around lines 27–29):** Instead of a single `joblib.dump(nn, index_dir / "nn.joblib")`, loop over `nn_by_metric` and save each model with a distinct name, e.g. `nn_euclidean.joblib`, `nn_manhattan.joblib`, `nn_cosine.joblib` (use the metric name in the filename).
  - **Optional but useful:** Write a small file (e.g. `metrics.txt`) that lists the metric names (one per line). Then at load time you know which `nn_<metric>.joblib` files to load.

- **`load_index`**
  - **Return value:** Instead of returning a single `nn`, load all saved NN models into a dict (e.g. `nn_by_metric`) and return `(scaler, nn_by_metric, vectors, metadata)`.
  - **How:** If you saved `metrics.txt`, read it and for each metric load `nn_<metric>.joblib` into the dict. If you didn’t add `metrics.txt`, you can instead look for every file matching `nn_*.joblib` in the index dir and build the list of metrics from the filenames.

---

## 4. Query: recommend with each metric and format three blocks

**File:** `src/recommend/query.py`

**What to do:** Run KNN for **each** metric and format the output as three sections (Euclidean, Manhattan, Cosine).

- **`recommend` function (around lines 41–70)**
  - **Signature:** Change the second parameter from `nn: NearestNeighbors` to `nn_by_metric` (dict: metric name → `NearestNeighbors`).
  - **Logic:** Keep the same steps for finding the query song row (`find_song_row`). Then, instead of a single `nn.kneighbors(...)`, loop over `nn_by_metric`. For each metric, run `kneighbors` with that model on the same query vector, exclude the query from the neighbor list, and build a small DataFrame of recommendations for that metric.
  - **Return value:** Return `(recs_by_metric, None)` where `recs_by_metric` is a dict mapping metric name (str) to a DataFrame of recommendations (same columns as now: title, artist_name, genre, etc.). On “song not found”, still return `(None, error_message)`.

- **`format_recommendations` function (around lines 73–85)**
  - **Signature:** Change the argument from `recs: pd.DataFrame` to `recs_by_metric: dict` (metric name → DataFrame of recommendations).
  - **Logic:** Loop over the dict. For each metric, add a heading (e.g. `"--- Euclidean ---"`) and then the same formatting you use now for one DataFrame (e.g. “Here are your 5 recommendations:” and the numbered list of title — artist). So the final string has three clear blocks, one per metric.

---

## 5. Build script: pass dict to save_index

**File:** `scripts/build_index_from_summary.py`

**What to do:** The build step now returns `(scaler, nn_by_metric, X_scaled, metadata)` instead of `(scaler, nn, ...)`.

- **Where (around lines 75–80):** Update the unpacking of `build_index`’s return value to use `nn_by_metric` (or similar name).
- **Where:** The call to `save_index` must pass that dict as the second argument instead of a single `nn`.

---

## 6. Recommend script: load dict and pass it to recommend + format

**File:** `scripts/recommend.py`

**What to do:** Load the index (which now gives a dict of NN models), call `recommend` with that dict, and pass the returned dict of recommendations to `format_recommendations`.

- **Where (around line 47):** `load_index` now returns `(scaler, nn_by_metric, vectors, metadata)`. Update the variable that receives the second value (e.g. `nn_by_metric`).
- **Where (around lines 61–72):** Pass `nn_by_metric` into `recommend` instead of `nn`. The return value is now `(recs_by_metric, err)` when successful. Pass `recs_by_metric` to `format_recommendations(recs_by_metric)` and print the result.

---

## Summary checklist

| File | Change |
|------|--------|
| `config/settings.py` | Add `METRICS = ["euclidean", "manhattan", "cosine"]`. |
| `src/index/build.py` | Build one `NearestNeighbors` per metric; return `(scaler, nn_by_metric, X_scaled, metadata)`. |
| `src/index/store.py` | `save_index`: accept `nn_by_metric`, save one `.joblib` per metric (+ optional `metrics.txt`). `load_index`: load all into `nn_by_metric`, return `(scaler, nn_by_metric, vectors, metadata)`. |
| `src/recommend/query.py` | `recommend`: accept `nn_by_metric`, run KNN per metric, return `(recs_by_metric, None)`. `format_recommendations`: accept `recs_by_metric`, print three sections (one per metric). |
| `scripts/build_index_from_summary.py` | Unpack `nn_by_metric` from `build_index`; pass it to `save_index`. |
| `scripts/recommend.py` | Unpack `nn_by_metric` from `load_index`; pass it to `recommend`; pass result to `format_recommendations`. |

After these changes, rebuilding the index will create one NN model per metric, and running the recommend script will print Euclidean, Manhattan, and Cosine recommendations one after the other so you can compare them.
