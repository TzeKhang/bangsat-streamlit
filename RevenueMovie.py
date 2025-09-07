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

    # Check required columns
    if "title" not in movies.columns or "revenue" not in movies.columns:
        raise ValueError("CSV must contain 'title' and 'revenue' columns.")

    # Replace missing revenue with median
    movies['revenue'] = movies['revenue'].fillna(movies['revenue'].median())

    # Fake "user interactions" for demo:
    #   In practice, this should come from ratings or watch history
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

    # Add item features (e.g. revenue bucket)
    movies["revenue_bucket"] = pd.qcut(movies["revenue"], 5, labels=False)
    dataset.fit_partial(
        items=movies["title"].unique(),
        item_features=["revenue_" + str(r) for r in movies["revenue_bucket"].unique()]
    )
    item_features = dataset.build_item_features(
        [(row["title"], ["revenue_" + str(row["revenue_bucket"])]) for _, row in movies.iterrows()]
    )

    # Train model
    model = LightFM(loss="warp")
    model.fit(interactions, item_features=item_features, epochs=15, num_threads=2)

    return model, dataset, item_features


# ---------------- Recommend Movies ----------------
def recommend(model, dataset, item_features, user_id, movies, n=10):
    n_users, n_items = dataset.interactions_shape()
    scores = model.predict(user_id, np.arange(n_items), item_features=item_features)
    top_items = np.argsort(-scores)[:n]

    item_labels = list(dataset.mapping()[2].keys())
    recommended = [item_labels[i] for i in top_items]

    return movies[movies["title"].isin(recommended)].copy()


# ---------------- STREAMLIT UI ----------------
def main():
    st.title("🎬 Revenue-based Movie Recommender (LightFM Hybrid)")

    # Load data
    movies, interactions_df = load_data()

    # Train LightFM
    model, dataset, item_features = build_model(movies, interactions_df)

    st.subheader("Available Movies")
    st.dataframe(movies[["title", "revenue"]].head(20), width=800, height=400)

    # User ID selection
    user_id = st.number_input("👤 Enter your User ID (0–49)", min_value=0, max_value=49, value=0)

    if st.button("📌 Show Recommendations"):
        recs = recommend(model, dataset, item_features, user_id, movies, n=10)

        st.subheader("🎯 Recommended Movies for You")
        st.dataframe(recs[["title", "revenue"]], width=800, height=400)

    # Evaluate precision
    if st.button("📊 Evaluate Model Precision"):
        n_users, n_items = dataset.interactions_shape()
        prec = precision_at_k(model, dataset.build_interactions(
            [(row["user"], row["item"]) for _, row in interactions_df.iterrows()]
        )[0], k=5).mean()
        st.success(f"Average Precision@5: {prec:.2f}")


if __name__ == "__main__":
    main()
