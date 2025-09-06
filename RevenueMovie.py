import streamlit as st
import pandas as pd
import numpy as np
from statistics import mean, median, mode, StatisticsError

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
        """Recommend movies within ±30% popularity range"""
        if not locked_range:
            lower = popularity * 0.7
            upper = popularity * 1.3
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
            🎯 Select up to 5 movies and get smart recommendations ✨
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
st.subheader("🎥 Select Movies You Watched (Max 5)")

selected_indices = []
for i, row in st.session_state["sample_movies"].iterrows():
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write(f"**{row['title']}** (Popularity: {row['popularity']:.2f})")
    with col2:
        if st.checkbox("Select", key=f"movie_{i}", value=(row['title'] in st.session_state["selected_movies"])):
            selected_indices.append(i)

selected_titles = st.session_state["sample_movies"].iloc[selected_indices]['title'].tolist()
if len(selected_titles) > 5:
    st.warning("⚠️ You can only select up to 5 movies.")
    selected_titles = selected_titles[:5]

st.session_state["selected_movies"] = selected_titles

if st.session_state["selected_movies"]:
    st.info(f"✅ Selected Movies: {', '.join(st.session_state['selected_movies'])}")


# ================== Buttons: Show + Refresh ==================
colA, colB = st.columns([1, 1])
with colA:
    show_recs = st.button("📌 Show Recommendations")
with colB:
    refresh_list = st.button("🔄 Refresh Movie List")

# Refresh list of initial movies
if refresh_list:
    st.session_state["sample_movies"] = recommender.movies.sample(min(20, len(recommender.movies))).reset_index(drop=True)


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
    st.subheader("🎯 Recommended Movies")

    rec_indices = []
    for i, row in st.session_state["recommendations"].reset_index(drop=True).iterrows():
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"**{row['title']}** (Popularity: {row['popularity']:.2f})")
        with col2:
            if st.checkbox("Choose", key=f"rec_{i}", value=(row['title'] in st.session_state["selected_recommended"])):
                rec_indices.append(i)

    selected_recs = st.session_state["recommendations"].iloc[rec_indices]['title'].tolist()
    if len(selected_recs) > 5:
        st.warning("⚠️ You can only choose up to 5 recommended movies.")
        selected_recs = selected_recs[:5]

    st.session_state["selected_recommended"] = selected_recs

    if st.session_state["selected_recommended"]:
        st.success(f"✨ Chosen from recommendations: {', '.join(st.session_state['selected_recommended'])}")

        # Capture user preferences for future reference
        chosen = st.session_state["recommendations"][
            st.session_state["recommendations"]["title"].isin(st.session_state["selected_recommended"])
        ]
        st.session_state["user_preferences"].extend(chosen.to_dict('records'))

    # Show recommendations table
    st.dataframe(
        st.session_state["recommendations"].set_index("title"),
        use_container_width=True
    )

    # Refresh recommendations button
    if st.button("🔄 Refresh Recommendations"):
        st.session_state["recommendations"] = st.session_state["recommendations"].sample(frac=1).reset_index(drop=True)

    # Stats of user preferences
    if st.session_state["selected_recommended"]:
        pops = chosen["popularity"].values
        try:
            mode_pop = mode(pops)
        except StatisticsError:
            mode_pop = "No unique mode"

        st.subheader("📊 Your Popularity Preferences (Stats)")
        st.write(f"**Mean:** {mean(pops):.2f}")
        st.write(f"**Median:** {median(pops):.2f}")
        st.write(f"**Mode:** {mode_pop}")
        st.write(f"**Standard Deviation:** {np.std(pops):.2f}")
