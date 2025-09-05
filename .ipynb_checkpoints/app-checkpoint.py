import streamlit as st
import pandas as pd

# Import team members' modules (classes)
# from module.popular import PopularRecommender
# from module.rating import RatingRecommender
# from module.genre import GenreRecommender

# Load MovieLens data
movies = pd.read_csv("dataset/movies.csv")
ratings = pd.read_csv("dataset/ratings.csv")

st.title("🎬 Movie Recommender System")

option = st.selectbox("Choose a Recommendation Type", ["Top 5 Most-Selling Movies", "Top 5 Highest-Rated Movies", "Top 5 Movies by Genre"])

if option == "Top 5 Most-Selling Movies":
    # Count how many ratings each movie has = popularity
    sales = ratings['movieId'].value_counts().reset_index()
    sales.columns = ['movieId', 'sales_count']
    top_sales = sales.merge(movies, on='movieId')
    st.subheader("Top 5 Most-Selling Movies")
    st.dataframe(top_sales[['title', 'sales_count']].head(5))

elif option == "Top 5 Highest-Rated Movies":
    avg_rating = ratings.groupby('movieId')['rating'].mean().reset_index()
    avg_rating.columns = ['movieId', 'avg_rating']
    top_rated = avg_rating.merge(movies, on='movieId')
    top_rated = top_rated.sort_values(by='avg_rating', ascending=False)
    st.subheader("Top 5 Highest-Rated Movies")
    st.dataframe(top_rated[['title', 'avg_rating']].head(5))

elif option == "Top 5 Movies by Genre":
    genre = st.text_input("Enter a genre (e.g., Action, Comedy, Drama):")
    if genre:
        genre_movies = movies[movies['genres'].str.contains(genre, case=False, na=False)]
        avg_rating = ratings.groupby('movieId')['rating'].mean().reset_index()
        genre_rated = genre_movies.merge(avg_rating, on='movieId')
        genre_rated = genre_rated.sort_values(by='rating', ascending=False)
        st.subheader(f"Top 5 {genre} Movies")
        st.dataframe(genre_rated[['title', 'genres', 'rating']].head(5))
