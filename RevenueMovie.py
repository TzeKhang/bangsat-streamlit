# RevenueMovie.py

import streamlit as st
import pandas as pd
import numpy as np

class RevenueRecommender:
    def __init__(self, movies_file):
        # Load dataset
        self.movies = pd.read_csv(movies_file)

        # Check required columns
        if "title" not in self.movies.columns or "revenue" not in self.movies.columns:
            raise ValueError("CSV must contain 'title' and 'revenue' columns.")

        # Clean dataset
        self.movies = self.movies[['title', 'revenue']].dropna()
        self.movies = self.movies[self.movies['revenue'] > 0].reset_index(drop=True)

    def recommend_by_revenue(self, revenue, locked_range=None):
        """Recommend movies within ±30% revenue range"""
        if not locked_range:
            lower = revenue * 0.7
            upper = revenue * 1.3
        else:
            lower, upper = locked_range

        candidates = self.movies[
            (self.movies['revenue'] >= lower) & (self.movies['revenue'] <= upper)
        ]
        return candidates[['title', 'revenue']], (lower, upper)


# ---------------- STREAMLIT APP ----------------
st.markdown(
    """
    <div style='text-align: center;'>
        <h1 style='color: #FF4B4B; margin-bottom: 0; white-space: nowrap;'>
            🎬 Movie Recommender System 🎬
        </h1>
        <h2 style='color: #FF4B4B; margin-top: 5px;'>
            Revenue Explorer
        </h2>
        <h3 style='color: #444; font-weight: normal; margin-top: 5px;'>
            💰 Discover Movies with Similar Revenue 💰 <br>
            🎯 Select up to 5 movies and get smart recommendations ✨
        </h3>
        <hr style='border: 1px solid #ddd; margin-top: 10px;'>
    </div>
    """,
    unsafe_allow_html=True
)

# Initialize recommender
recommender = RevenueRecommender("dataset/RevenueMovies.csv")

# Session state
if "locked_range" not in st.session_state:
    st.session_state["locked_range"] = None
if "selected_movies" not in st.session_state:
    st.session_state["selected_movies"] = []
if "recommendations" not in st.session_state:
    st.session_state["recommendations"] = pd.DataFrame()
if "feedback_log" not in st.session_state:
    st.session_state["feedback_log"] = []
if "show_summary" not in st.session_state:
    st.session_state["show_summary"] = False
if "sample_movies" not in st.session_state:
    st.session_state["sample_movies"] = recommender.movies.sample(min(20, len(recommender.movies))).reset_index(drop=True)
if "selected_recommended" not in st.session_state:
    st.session_state["selected_recommended"] = []


# ================== Movie Selection ==================
st.subheader("🎥 Select Movies You Watched (Max 5)")

selected_indices = []
for i, row in st.session_state["sample_movies"].iterrows():
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write(f"**{row['title']}** (Revenue: ${row['revenue']:,})")
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
        recs, locked = recommender.recommend_by_revenue(row['revenue'], st.session_state["locked_range"])
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
            st.write(f"**{row['title']}** (Revenue: ${row['revenue']:,})")
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

    # Refresh recommendations button
    if st.button("🔄 Refresh Recommendations"):
        st.session_state["recommendations"] = st.session_state["recommendations"].sample(frac=1).reset_index(drop=True)


# ================== Budget Preference Clustering ==================
if st.session_state["selected_recommended"]:
    st.subheader("💡 Budget Preference Clustering")

    chosen = st.session_state["recommendations"][
        st.session_state["recommendations"]["title"].isin(st.session_state["selected_recommended"])
    ]

    if not chosen.empty:
        revenues = chosen["revenue"].values
        avg_rev = np.mean(revenues)
        std_rev = np.std(revenues)

        st.write(f"**Average Revenue:** ${avg_rev:,.0f}")
        st.write(f"**Revenue Consistency (Std Dev):** ${std_rev:,.0f}")

        if std_rev < avg_rev * 0.3:
            st.success("✅ Your selections show a **consistent budget preference**.")
        else:
            st.warning("⚠️ Your selections show a **wide budget range**.")


# ================== Sidebar: Satisfaction Summary ==================
if st.sidebar.button("📊 Toggle Satisfaction Summary"):
    st.session_state["show_summary"] = not st.session_state["show_summary"]

if st.session_state["show_summary"]:
    st.sidebar.header("📊 User Satisfaction Summary")
    total_recs = sum(len(f["recommendations"]) for f in st.session_state["feedback_log"])
    total_likes = sum(len(f["liked"]) for f in st.session_state["feedback_log"])

    if total_recs > 0:
        precision = total_likes / total_recs
        st.sidebar.write(f"**Total recommendations shown:** {total_recs}")
        st.sidebar.write(f"**Total movies liked:** {total_likes}")
        st.sidebar.write(f"**Precision (Liked ÷ Recommended):** {precision:.2f}")
    else:
        st.sidebar.info("No feedback collected yet.")
