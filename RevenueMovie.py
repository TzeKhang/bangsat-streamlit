# RevenueMovieLightFM.py

import streamlit as st
import pandas as pd
import numpy as np
from lightfm import LightFM
from lightfm.data import Dataset
from lightfm.evaluation import precision_at_k
import random

# ---------------- Load Data ----------------
@st.cache_data
def load_data():
    movies = pd.read_csv("dataset/RevenueMovies.csv")

    # Ensure revenue column is numeric
    movies['revenue'] = pd.to_numeric(movies['revenue'], errors='coerce').fillna(0)
    movies['budget'] = pd.to_numeric(movies['budget'], errors='coerce').fillna(0)
    movies['runtime'] = pd.to_numeric(movies['runtime'], errors='coerce').fillna(0)
    movies['vote_average'] = pd.to_numeric(movies['vote_average'], errors='coerce').fillna(0)
    movies['popularity'] = pd.to_numeric(movies['popularity'], errors='coerce').fillna(0)

    # Fake interactions (replace with real ratings if available)
    n_users = 50
    interactions = []
    for user in range(n_users):
        liked_movies = random.sample(range(len(movies)), 10)
        for m in liked_movies:
            interactions.append((user, movies.loc[m, "title"], 1))

    interactions_df = pd.DataFrame(interactions, columns=["user", "item", "rating"])
    return movies, interactions_df


# ---------------- Build LightFM Model ----------------
def build_model(movies, interactions_df):
    dataset = Dataset()

    # Fit users and items
    dataset.fit(
        users=interactions_df["user"].unique(),
        items=movies["title"].unique()
    )

    # Build user-item interaction matrix
    (interactions, weights) = dataset.build_interactions(
        [(row["user"], row["item"]) for _, row in interactions_df.iterrows()]
    )

    # ---- Item Features ----
    item_features_list = []

    # Revenue buckets
    movies["revenue_bucket"] = pd.qcut(movies["revenue"], 5, labels=False, duplicates="drop")
    item_features_list += ["revenue_" + str(r) for r in movies["revenue_bucket"].unique()]

    # Budget buckets
    movies["budget_bucket"] = pd.qcut(movies["budget"], 5, labels=False, duplicates="drop")
    item_features_list += ["budget_" + str(b) for b in movies["budget_bucket"].unique()]

    # Vote average buckets
    movies["vote_bucket"] = pd.qcut(movies["vote_average"], 5, labels=False, duplicates="drop")
    item_features_list += ["vote_" + str(v) for v in movies["vote_bucket"].unique()]

    # Genres
    all_genres = set()
    movies["genres"] = movies["genres"].fillna("")
    for g_list in movies["genres"].str.split("|"):
        all_genres.update(g_list)
    all_genres = [g for g in all_genres if g.strip() != ""]
    item_features_list += list(all_genres)

    # Register item features
    dataset.fit_partial(
        items=movies["title"].unique(),
        item_features=item_features_list
    )

    # Build item features mapping
    def movie_features(row):
        feats = []
        feats.append("revenue_" + str(row["revenue_bucket"]))
        feats.append("budget_" + str(row["budget_bucket"]))
        feats.append("vote_" + str(row["vote_bucket"]))
        for g in row["genres"].split("|"):
            if g.strip() != "":
                feats.append(g.strip())
        return (row["title"], feats)

    item_features = dataset.build_item_features(
        [movie_features(row) for _, row in movies.iterrows()]
    )

    # Train LightFM model
    model = LightFM(loss="warp")
    model.fit(interactions, item_features=item_features, epochs=20, num_threads=4)

    return model, dataset, item_features


# ---------------- Recommend Movies ----------------
def recommend(model, dataset, item_features, user_id, movies, n=10):
    n_users, n_items = dataset.interactions_shape()
    scores = model.predict(user_id, np.arange(n_items), item_features=item_features)
    top_items = np.argsort(-scores)[:n]

    item_labels = list(dataset.mapping()[2].keys())  # index → title
    recommended = [item_labels[i] for i in top_items]

    return movies[movies["title"].isin(recommended)].copy()


# ---------------- STREAMLIT UI ----------------
def main():
    st.title("🎬 Revenue-based Movie Recommender (LightFM Hybrid)")

    # Load data
    movies, interactions_df = load_data()

    # Train model
    with st.spinner("Training LightFM model... ⏳"):
        model, dataset, item_features = build_model(movies, interactions_df)

    # Show movie samples
    st.subheader("Available Movies")
    st.dataframe(movies[["title", "genres", "budget", "revenue", "vote_average", "popularity"]].head(20),
                 width=1000, height=400)

    # Select user
    user_id = st.number_input("👤 Enter your User ID (0–49)", min_value=0, max_value=49, value=0)

    if st.button("📌 Show Recommendations"):
        recs = recommend(model, dataset, item_features, user_id, movies, n=10)
        st.subheader("🎯 Recommended Movies")
        st.dataframe(recs[["title", "genres", "budget", "revenue", "vote_average", "popularity"]],
                     width=1000, height=400)

    # Model evaluation
    if st.button("📊 Evaluate Model Precision"):
        n_users, n_items = dataset.interactions_shape()
        prec = precision_at_k(model, dataset.build_interactions(
            [(row["user"], row["item"]) for _, row in interactions_df.iterrows()]
        )[0], k=5).mean()
        st.success(f"Average Precision@5: {prec:.2f}")


if __name__ == "__main__":
    main()
