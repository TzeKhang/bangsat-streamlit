# RevenueMovie.py

import streamlit as st
import pandas as pd

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


# ================== Movie Selection ==================
st.subheader("🎥 Select Movies You Watched (Max 5)")

# Display movie table with checkbox selection
selected_indices = []
for i, row in st.session_state["sample_movies"].iterrows():
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write(f"**{row['title']}** (Revenue: ${row['revenue']:,})")
    with col2:
        if st.checkbox("Select", key=f"movie_{i}", value=(row['title'] in st.session_state["selected_movies"])):
            selected_indices.append(i)

# Update selected movies (limit 5)
selected_titles = st.session_state["sample_movies"].iloc[selected_indices]['title'].tolist()
if len(selected_titles) > 5:
    st.warning("⚠️ You can only select up to 5 movies.")
    selected_titles = selected_titles[:5]
st.session_state["selected_movies"] = selected_titles

# Show current selection
if st.session_state["selected_movies"]:
    st.info(f"✅ Selected Movies: {', '.join(st.session_state['selected_movies'])}")


# ================== Recommendations ==================
if st.button("📌 Show Recommendations"):
    all_recs = pd.DataFrame()
    for title in st.session_state["selected_movies"]:
        row = recommender.movies[recommender.movies['title'] == title].iloc[0]
        recs, locked = recommender.recommend_by_revenue(row['revenue'], st.session_state["locked_range"])
        st.session_state["locked_range"] = locked  # Lock range after first
        recs = recs[recs['title'] != title]  # remove the selected movie itself
        all_recs = pd.concat([all_recs, recs])

    if not all_recs.empty:
        st.session_state["recommendations"] = all_recs.drop_duplicates().sample(min(5, len(all_recs)))
    else:
        st.session_state["recommendations"] = pd.DataFrame()

# Display recommendations
if not st.session_state["recommendations"].empty:
    st.subheader("🎯 Recommended Movies")
    st.table(st.session_state["recommendations"].reset_index(drop=True))


# ================== Refresh Movie List ==================
if st.button("🔄 Refresh Movie List"):
    st.session_state["sample_movies"] = recommender.movies.sample(min(20, len(recommender.movies))).reset_index(drop=True)


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
