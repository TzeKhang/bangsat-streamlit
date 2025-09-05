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
            Or Refresh for More Hidden Gems ✨
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

# Center: Pick multiple movies
st.header("🎥 Pick Movies You Watched")
sample_movies = recommender.movies.sample(min(20, len(recommender.movies))).reset_index(drop=True)

selected_movies = st.multiselect(
    "Select one or more movies:",
    sample_movies['title'].tolist()
)

if st.button("Confirm Selection"):
    if selected_movies:
        # Average revenue of chosen movies
        selected_revenue = sample_movies[sample_movies['title'].isin(selected_movies)]['revenue'].mean()

        st.session_state["selected_movies"] = selected_movies

        # Lock range if not set
        if not st.session_state["locked_range"]:
            st.session_state["locked_range"] = (selected_revenue * 0.7, selected_revenue * 1.3)

        # Get recommendations
        recs, _ = recommender.recommend_by_revenue(selected_revenue, st.session_state["locked_range"])
        st.session_state["recommendations"] = recs.sample(min(10, len(recs))).reset_index(drop=True)

# Main content
if st.session_state["selected_movies"]:
    st.subheader(f"🎬 Since you watched {', '.join(st.session_state['selected_movies'])}, you might also like:")

    # Refresh button
    if st.button("🔄 Refresh Recommendations"):
        avg_revenue = st.session_state["recommendations"]['revenue'].mean()
        recs, _ = recommender.recommend_by_revenue(avg_revenue, st.session_state["locked_range"])
        st.session_state["recommendations"] = recs.sample(min(10, len(recs))).reset_index(drop=True)

    # Show recommendations in a table
    if not st.session_state["recommendations"].empty:
        rec_table = st.session_state["recommendations"].copy()
        rec_table = rec_table.rename(columns={'title': 'Movie Title', 'revenue': 'Revenue ($)'})
        rec_table['Revenue ($)'] = rec_table['Revenue ($)'].apply(lambda x: f"${x:,.0f}")

        st.dataframe(rec_table, width=1000, height=500)

        # Like button
        liked_movies = st.multiselect(
            "👍 Select the movies you liked from the recommendations:",
            rec_table['Movie Title'].tolist()
        )

        if st.button("Save Feedback"):
            st.session_state["feedback_log"].append({
                "watched": st.session_state["selected_movies"],
                "recommendations": list(rec_table['Movie Title']),
                "liked": liked_movies
            })
            st.success("✅ Feedback saved!")

# Sidebar: Satisfaction Summary
st.sidebar.header("📊 Evaluation")
if st.sidebar.button("Show Satisfaction Summary"):
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
