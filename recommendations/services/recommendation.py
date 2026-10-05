import os
import pickle
from functools import lru_cache

import pandas as pd

from django.conf import settings

# ============================================================
# PATHS
# ============================================================

BASE_DIR = settings.BASE_DIR

DATA_PATH = os.path.join(BASE_DIR, "data_ml", "movie_dataset_final.csv")

TFIDF_PATH = os.path.join(BASE_DIR, "ml_models", "tfidf_vectorizer.pkl")


# ============================================================
# LOAD ML DATASET
# ============================================================

movies = pd.read_csv(DATA_PATH)

movies = movies.reset_index(drop=True)


# ============================================================
# LOAD TF-IDF MODEL
# ============================================================

with open(TFIDF_PATH, "rb") as f:
    tfidf = pickle.load(f)


# ============================================================
# CREATE TF-IDF MATRIX
# ============================================================

tfidf_matrix = tfidf.transform(movies["tags"].fillna(""))


# ============================================================
# RECOMMENDATION
# ============================================================


@lru_cache(maxsize=256)
def recommend(movie_title, n=10):

    # --------------------------------------------------------
    # Find movie
    # --------------------------------------------------------

    matches = movies.index[
        movies["title"].astype(str).str.strip().str.lower()
        == movie_title.strip().lower()
    ]

    if len(matches) == 0:
        return []

    # If duplicate title exists, use first occurrence
    movie_index = int(matches[0])

    # --------------------------------------------------------
    # Get cluster
    # --------------------------------------------------------

    movie_cluster = int(movies.loc[movie_index, "svd_cluster"])

    # --------------------------------------------------------
    # Get movies from same cluster
    # --------------------------------------------------------

    same_cluster_indices = movies.index[movies["svd_cluster"] == movie_cluster].tolist()

    # --------------------------------------------------------
    # Calculate similarity
    # --------------------------------------------------------

    selected_vector = tfidf_matrix[movie_index]

    cluster_vectors = tfidf_matrix[same_cluster_indices]

    similarity_scores = (selected_vector @ cluster_vectors.T).toarray().flatten()

    # --------------------------------------------------------
    # Combine index + score
    # --------------------------------------------------------

    scores = list(zip(same_cluster_indices, similarity_scores))

    # Remove selected movie
    scores = [(index, score) for index, score in scores if index != movie_index]

    # Sort highest similarity first
    scores.sort(key=lambda x: x[1], reverse=True)

    # Top N
    top_scores = scores[:n]

    # --------------------------------------------------------
    # Return results
    # --------------------------------------------------------

    recommendations = []

    for index, score in top_scores:

        recommendations.append(
            {
                "title": movies.loc[index, "title"],
                "similarity": round(float(score), 4),
                "cluster": int(movies.loc[index, "svd_cluster"]),
            }
        )

    return recommendations
