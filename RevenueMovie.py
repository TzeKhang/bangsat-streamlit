# RevenueMovie.py

import streamlit as st
import pandas as pd
import random

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
            Or Refresh for More Hidden Gems ✨
        </h3>
        <hr style='border: 1px solid #ddd; margin-top: 10px;'>
    </div>
    """,
    unsafe_allow_html=True
)

# Initialize recommender
recommender = RevenueRecommender("RevenueMovies.csv")

# Session state
if "locked_range" not in st.session_state:
    st.session_state["locked_range"] = None
if "selected_movie" not in st.session_state:
    st.session_state["selected_movie"] = None
if "recommendations" not in st.session_state:
    st.session_state["recommendations"] = pd.DataFrame()
if "feedback_log" not in st.session_state:
    st.session_state["feedback_log"] = []

# Sidebar: Pick a movie
st.sidebar.header("🎥 Pick a Movie")
sample_movies = recommender.movies.sample(min(20, len(recommender.movies))).reset_index(drop=True)
movie_choice = st.sidebar.radio(
    "Select a movie you watched:",
    sample_movies['title']
)

if st.sidebar.button("Confirm Selection"):
    selected_row = sample_movies[sample_movies['title'] == movie_choice].iloc[0]
    st.session_state["selected_movie"] = selected_row['title']
    selected_revenue = selected_row['revenue']

    # Lock range if not set
    if not st.session_state["locked_range"]:
        st.session_state["locked_range"] = (selected_revenue * 0.7, selected_revenue * 1.3)

    # Get recommendations
    recs, _ = recommender.recommend_by_revenue(selected_revenue, st.session_state["locked_range"])
    st.session_state["recommendations"] = recs.sample(min(5, len(recs))).reset_index(drop=True)

# Main content
if st.session_state["selected_movie"]:
    st.subheader(f"🎬 Since you watched **{st.session_state['selected_movie']}**, you might also like:")

    # Refresh button
    if st.button("🔄 Refresh Recommendations"):
        recs, _ = recommender.recommend_by_revenue(
            st.session_state["recommendations"]['revenue'].mean(),
            st.session_state["locked_range"]
        )
        st.session_state["recommendations"] = recs.sample(min(5, len(recs))).reset_index(drop=True)

    # Show recommendations
    if not st.session_state["recommendations"].empty:
        liked_movies = []
        for i, row in st.session_state["recommendations"].iterrows():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**{row['title']}** (Revenue: ${row['revenue']:,})")
            with col2:
                if st.button(f"👍 Like {row['title']}", key=row['title']):
                    liked_movies.append(row['title'])

        # Save feedback
        if liked_movies:
            st.session_state["feedback_log"].append({
                "watched": st.session_state["selected_movie"],
                "recommendations": list(st.session_state["recommendations"]['title']),
                "liked": liked_movies
            })
            st.success(f"✅ Feedback saved for {st.session_state['selected_movie']}")

# Satisfaction Summary
if st.sidebar.button("📊 Show Satisfaction Summary"):
    st.header("📊 User Satisfaction Summary")
    total_recs = sum(len(f["recommendations"]) for f in st.session_state["feedback_log"])
    total_likes = sum(len(f["liked"]) for f in st.session_state["feedback_log"])

    if total_recs > 0:
        precision = total_likes / total_recs
        st.write(f"**Total recommendations shown:** {total_recs}")
        st.write(f"**Total movies liked:** {total_likes}")
        st.write(f"**Precision (Liked ÷ Recommended):** {precision:.2f}")
    else:
        st.info("No feedback collected yet.")
