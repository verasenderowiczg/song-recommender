# app.py
import streamlit as st
from pathlib import Path
from src.index import load_index
from src.recommend import recommend, format_recommendations

# -----------------------
# 1. Load prebuilt index
# -----------------------
PROJECT_ROOT = Path(__file__).resolve().parent
INDEX_DIR = PROJECT_ROOT / "index"  # <-- full path relative to app.py

st.set_page_config(
    page_title="Music Recommender 🎵",
    page_icon="🎧",
    layout="centered"
)

st.title("🎶 Instant Music Recommender")

# Load index (only once)
@st.cache_resource
def load_recommender(index_dir):
    scaler, nn_by_metric, vectors, metadata = load_index(index_dir)
    return scaler, nn_by_metric, vectors, metadata

scaler, nn_by_metric, vectors, metadata = load_recommender(INDEX_DIR)

# -----------------------
# 2. Song selection
# -----------------------
song_list = sorted(metadata['title'].dropna().unique())
#selected_song = st.selectbox("🎵 Select a song:", song_list)
selected_song = st.text_input("🎵 Enter a song title:")
artist_name = st.text_input("🎤 Artist name (optional):", "")

# -----------------------
# 3. Recommendation
# -----------------------
if st.button("🚀 Recommend Similar Songs"):
    if not selected_song.strip():
        st.warning("Please select a song.")
    else:
        with st.spinner("Finding similar songs..."):
            recs_by_metric, err = recommend(
                scaler,
                nn_by_metric,
                vectors,
                metadata,
                song_name=selected_song,
                artist_name=artist_name if artist_name.strip() else None,
                top_k=5
            )

        if err:
            st.warning(err)
        else:
            st.success("🎶 Recommendations:")
            formatted = format_recommendations(recs_by_metric)
            st.text(formatted)