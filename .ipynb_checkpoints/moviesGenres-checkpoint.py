import streamlit as st
import pandas as pd
import re
import random

class GenreRecommender:
    def __init__(self, movies_file, ratings_file):
        # Load data
        self.movies = pd.read_csv(movies_file)
        self.ratings = pd.read_csv(ratings_file)

        # Extract year from title
        self.movies['year'] = self.movies['title'].apply(
            lambda x: int(re.search(r'\((\d{4})\)', x).group(1)) if re.search(r'\((\d{4})\)', x) else None
        )

        # Create clean title (without year)
        self.movies['clean_title'] = self.movies['title'].apply(
            lambda x: re.sub(r'\s*\(\d{4}\)', '', x)
        )

        # Compute average rating for each movie
        movie_stats = self.ratings.groupby('movieId').agg({'rating': 'mean'}).reset_index()
        movie_stats.columns = ['movieId', 'rating']

        # Merge stats into movies dataframe
        self.movies = self.movies.merge(movie_stats, on='movieId', how='left')

    def recommend(self, selected_genres, year_range):
        genre_movies = self.movies[
            self.movies['genres'].str.contains('|'.join(selected_genres), case=False, na=False)
        ]
        genre_movies = genre_movies[
            (genre_movies['year'] >= year_range[0]) & (genre_movies['year'] <= year_range[1])
        ]
        return genre_movies[['clean_title', 'genres', 'year', 'rating']]

# ---------------- STREAMLIT APP ----------------
st.markdown(
    """
    <div style='text-align: center;'>
        <h1 style='color: #FF4B4B; margin-bottom: 0; white-space: nowrap;'>
            🍿 Movie Recommender System 🍿
        </h1>
        <h2 style='color: #FF4B4B; margin-top: 5px;'>
            Genres Explorer
        </h2>
        <h3 style='color: #444; font-weight: normal; margin-top: 5px;'>
            🎬 Pick your favorite genres 🎬 <br>
            Or Let Us Surprise You With A Hidden Gem ✨
        </h3>
        <hr style='border: 1px solid #ddd; margin-top: 10px;'>
    </div>
    """,
    unsafe_allow_html=True
)

# Initialize recommender
recommender = GenreRecommender("dataset/movies.csv", "dataset/ratings.csv")

# Initialize session state
if "filtered_movies" not in st.session_state:
    st.session_state["filtered_movies"] = pd.DataFrame()

# User input: genre selection
all_genres = sorted(set(g for gs in recommender.movies['genres'].dropna().str.split('|') for g in gs))
selected_genres = st.multiselect("🎭 Select genres:", all_genres, default=[])

# User input: year range
min_year, max_year = int(recommender.movies['year'].min()), int(recommender.movies['year'].max())
year_range = st.slider(
    "📅 Select year range:",
    min_value=min_year,
    max_value=max_year,
    value=(min_year, max_year)
)

# ---------------- Show Recommendations ----------------
if st.button("📌 Show Recommendations"):
    if selected_genres:
        filtered = recommender.recommend(selected_genres, year_range)
    else:
        filtered = recommender.movies[
            (recommender.movies['year'] >= year_range[0]) & (recommender.movies['year'] <= year_range[1])
        ]

    st.session_state["filtered_movies"] = filtered

# Display table if filtered data exists
if not st.session_state["filtered_movies"].empty:
    filtered_movies_display = st.session_state["filtered_movies"].copy()
    filtered_movies_display['year'] = filtered_movies_display['year'].astype(int)
    filtered_movies_display = filtered_movies_display[['clean_title', 'genres', 'year']]
    filtered_movies_display = filtered_movies_display.rename(columns={
        'clean_title': 'Movies Title',
        'genres': 'Genres',
        'year': 'Year'
    })

    # Summary
    st.info(f"Found {len(filtered_movies_display)} movies matching your selection ({year_range[0]}–{year_range[1]})")

    # Sort dropdown
    sort_option = st.selectbox(
        "🔃 Sort movies by:",
        options=["Title (A-Z)", "Year (Ascending)", "Year (Descending)", "Random"]
    )

    # Apply sorting
    if sort_option == "Title (A-Z)":
        filtered_movies_display = filtered_movies_display.sort_values(by='Movies Title', ascending=True)
    elif sort_option == "Year (Ascending)":
        filtered_movies_display = filtered_movies_display.sort_values(by='Year', ascending=True)
    elif sort_option == "Year (Descending)":
        filtered_movies_display = filtered_movies_display.sort_values(by='Year', ascending=False)
    elif sort_option == "Random":
        filtered_movies_display = filtered_movies_display.sample(frac=1).reset_index(drop=True)

    st.dataframe(filtered_movies_display, width=1200, height=800)

# ---------------- Surprise Me ----------------
if st.button("🎲 Surprise Me With RANDOM Suggestion !"):
    if selected_genres:
        genre_movies = recommender.movies[
            recommender.movies['genres'].str.contains('|'.join(selected_genres), case=False, na=False)
        ]
    else:
        genre_movies = recommender.movies.copy()

    genre_movies = genre_movies[
        (genre_movies['year'] >= year_range[0]) & (genre_movies['year'] <= year_range[1])
    ]

    # Only movies with rating >= 4.0
    genre_movies = genre_movies[genre_movies['rating'] >= 4.0]

    if len(genre_movies) > 0:
        surprise = genre_movies.sample(1).iloc[0]
        title = surprise['clean_title']
        year = int(surprise['year'])
        rating = round(surprise['rating'], 2)
        genres = surprise['genres']

        st.success(
            f"🎉 Tonight’s Randomly Pick : **{title} ({year})** 🎬\n\n"
            f"⭐ Rating : {rating}\n\n"
            f"🎭 Genre : {genres}\n\n"
            f"🔥 Grab your popcorn and enjoy the show!"
        )
    else:
        st.warning("No movies found for this filter with rating >= 4.0.")