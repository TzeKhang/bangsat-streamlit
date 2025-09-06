import streamlit as st
import pandas as pd
import numpy as np

class PopularityRecommender:
    def __init__(self, movies_file):
        # Load dataset
        self.movies = pd.read_csv(movies_file)

        # Check required columns
        if "title" not in self.movies.columns or "popularity" not in self.movies.columns:
            raise ValueError("CSV must contain 'title' and 'popularity' columns.")

        # Clean dataset
        self.movies = self.movies[['title', 'popularity']].dropna()
        self.movies = self.movies[self.movies['popularity'] > 0].reset_index(drop=True)

    def recommend_by_popularity(self, popularity, locked_range=None):
        """Recommend movies within ±15% popularity range"""
        if not locked_range:
            lower = popularity * 0.85
            upper = popularity * 1.15
        else:
            lower, upper = locked_range

        candidates = self.movies[
            (self.movies['popularity'] >= lower) & (self.movies['popularity'] <= upper)
        ]
        return candidates[['title', 'popularity']], (lower, upper)


# ---------------- STREAMLIT APP ----------------
st.markdown(
    """
    <div style='text-align: center;'>
        <h1 style='color: #FF4B4B; margin-bottom: 0; white-space: nowrap;'>
            🎬 Movie Recommender System 🎬
        </h1>
        <h2 style='color: #FF4B4B; margin-top: 5px;'>
            Popularity Explorer
        </h2>
        <h3 style='color: #444; font-weight: normal; margin-top: 5px;'>
            🌟 Discover Movies with Similar Popularity 🌟 <br>
            🎯 Select up to 10 movies and get smart recommendations ✨
        </h3>
        <hr style='border: 1px solid #ddd; margin-top: 10px;'>
    </div>
    """,
    unsafe_allow_html=True
)

# Initialize recommender
recommender = PopularityRecommender("dataset/RevenueMovies.csv")

# Session state
if "locked_range" not in st.session_state:
    st.session_state["locked_range"] = None
if "selected_movies" not in st.session_state:
    st.session_state["selected_movies"] = []
if "recommendations" not in st.session_state:
    st.session_state["recommendations"] = pd.DataFrame()
if "sample_movies" not in st.session_state:
    st.session_state["sample_movies"] = recommender.movies.sample(min(20, len(recommender.movies))).reset_index(drop=True)
if "selected_recommended" not in st.session_state:
    st.session_state["selected_recommended"] = []
if "user_preferences" not in st.session_state:
    st.session_state["user_preferences"] = []


# ================== Movie Selection ==================
st.subheader("🎥 Select Movies You Watched (Max 10)")

# Keep previously selected movies always visible
selected_df = recommender.movies[recommender.movies['title'].isin(st.session_state["selected_movies"])]
remaining_df = st.session_state["sample_movies"][~st.session_state["sample_movies"]['title'].isin(st.session_state["selected_movies"])]
all_movies_to_show = pd.concat([selected_df, remaining_df]).drop_duplicates().reset_index(drop=True)

new_selected_movies = []
for i, row in all_movies_to_show.iterrows():
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write(f"**{row['title']}** (Popularity: {row['popularity']:.2f})")
    with col2:
        checked = st.checkbox("Select", key=f"movie_{row['title']}", value=(row['title'] in st.session_state["selected_movies"]))
        if checked:
            new_selected_movies.append(row['title'])

if len(new_selected_movies) > 10:
    st.warning("⚠️ You can only select up to 10 movies.")
    new_selected_movies = new_selected_movies[:10]

# Update session state with current checked movies
st.session_state["selected_movies"] = new_selected_movies

if st.session_state["selected_movies"]:
    st.info(f"✅ Selected Movies: {', '.join(st.session_state['selected_movies'])}")


# ================== Buttons: Show + Refresh ==================
colA, colB = st.columns([1, 1])
with colA:
    show_recs = st.button("📌 Show Recommendations")
with colB:
    refresh_list = st.button("🔄 Refresh Movie List")

# Refresh list of initial movies (keep selected intact)
if refresh_list:
    new_sample = recommender.movies.sample(min(20, len(recommender.movies))).reset_index(drop=True)
    # Ensure no duplicates with selected
    st.session_state["sample_movies"] = pd.concat([selected_df, new_sample]).drop_duplicates().reset_index(drop=True)


# ================== Recommendations ==================
if show_recs:
    all_recs = pd.DataFrame()
    st.session_state["locked_range"] = None  # reset lock when generating new recommendations
    for title in st.session_state["selected_movies"]:
        row = recommender.movies[recommender.movies['title'] == title].iloc[0]
        recs, locked = recommender.recommend_by_popularity(row['popularity'], st.session_state["locked_range"])
        st.session_state["locked_range"] = locked
        recs = recs[recs['title'] != title]
        all_recs = pd.concat([all_recs, recs])

    if not all_recs.empty:
        st.session_state["recommendations"] = all_recs.drop_duplicates().sample(min(10, len(all_recs)))
    else:
        st.session_state["recommendations"] = pd.DataFrame()


# Display recommendations
if not st.session_state["recommendations"].empty:
    st.subheader("🎯 Interested in any of the movies below? Tick to mark as interested, refresh if not interested")

    rec_indices = []
    for i, row in st.session_state["recommendations"].reset_index(drop=True).iterrows():
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"**{row['title']}** (Popularity: {row['popularity']:.2f})")
        with col2:
            if st.checkbox("Choose", key=f"rec_{row['title']}", value=(row['title'] in st.session_state["selected_recommended"])):
                rec_indices.append(i)

    selected_recs = st.session_state["recommendations"].iloc[rec_indices]['title'].tolist()
    if len(selected_recs) > 5:
        st.warning("⚠️ You can only choose up to 5 recommended movies.")
        selected_recs = selected_recs[:5]

    st.session_state["selected_recommended"] = selected_recs

    if st.session_state["selected_recommended"]:
        st.success(f"✨ Chosen from recommendations: {', '.join(st.session_state['selected_recommended'])}")

        # Capture user preferences for future reference
        chosen = st.session_state["recommendations"][st.session_state["recommendations"]["title"].isin(st.session_state["selected_recommended"])]
        st.session_state["user_preferences"].extend(chosen.to_dict('records'))

    # Refresh recommendations button (keep selections)
    if st.button("🔄 Refresh Recommendations"):
        st.session_state["recommendations"] = st.session_state["recommendations"].sample(frac=1).reset_index(drop=True)

    # ================== Precision Calculation ==================
    retrieved = len(st.session_state["recommendations"])
    relevant = len(st.session_state["selected_recommended"])

    if retrieved > 0:
        precision = relevant / retrieved
        st.subheader("📊 Recommendation Precision")
        st.metric("Precision", f"{precision:.2f}")
    else:
        st.info("No recommendations to calculate precision.")
