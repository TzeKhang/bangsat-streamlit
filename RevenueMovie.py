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
recommender = PopularityRecommender("dataset/PopularityMovies.csv")

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


# ================== Movie Selection ==================
st.subheader("🎥 Select Movies You Watched (Max 5)")

# Show in table form
selected = st.multiselect(
    "Choose up to 5 movies:",
    options=st.session_state["sample_movies"]["title"].tolist(),
    default=st.session_state["selected_movies"]
)

if len(selected) > 5:
    st.warning("⚠️ You can only select up to 5 movies.")
    selected = selected[:5]

st.session_state["selected_movies"] = selected

if st.session_state["selected_movies"]:
    st.info(f"✅ Selected Movies: {', '.join(st.session_state['selected_movies'])}")

st.dataframe(
    st.session_state["sample_movies"].set_index("title"),
    use_container_width=True
)


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

    rec_titles = st.multiselect(
        "Choose from recommendations (Max 5):",
        options=st.session_state["recommendations"]["title"].tolist(),
        default=st.session_state["selected_recommended"]
    )

    if len(rec_titles) > 5:
        st.warning("⚠️ You can only choose up to 5 recommended movies.")
        rec_titles = rec_titles[:5]

    st.session_state["selected_recommended"] = rec_titles

    if st.session_state["selected_recommended"]:
        st.success(f"✨ Chosen from recommendations: {', '.join(st.session_state['selected_recommended'])}")

    st.dataframe(
        st.session_state["recommendations"].set_index("title"),
        use_container_width=True
    )

    # Refresh recommendations button
    if st.button("🔄 Refresh Recommendations"):
        st.session_state["recommendations"] = st.session_state["recommendations"].sample(frac=1).reset_index(drop=True)


# ================== Budget Preference Clustering ==================
if st.session_state["selected_recommended"]:
    st.subheader("💡 Popularity Preference Clustering")

    chosen = st.session_state["recommendations"][
        st.session_state["recommendations"]["title"].isin(st.session_state["selected_recommended"])
    ]

    if not chosen.empty:
        pops = chosen["popularity"].values
        avg_pop = np.mean(pops)
        std_pop = np.std(pops)

        st.write(f"**Average Popularity:** {avg_pop:,.2f}")
        st.write(f"**Popularity Consistency (Std Dev):** {std_pop:,.2f}")

        if std_pop < avg_pop * 0.3:
            st.success("✅ Your selections show a **consistent popularity preference**.")
        else:
            st.warning("⚠️ Your selections show a **wide popularity range**.")
