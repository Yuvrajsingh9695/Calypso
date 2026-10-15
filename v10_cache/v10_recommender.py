from pathlib import Path
import pandas as pd
import numpy as np


def load_recommender(base_dir=None):
    if base_dir is None:
        base_dir = Path(__file__).resolve().parent
    else:
        base_dir = Path(base_dir)

    rec = pd.read_pickle(base_dir / "rec_v10.pkl")
    rec = rec.reset_index(drop=True)

    cache = pd.read_csv(base_dir / "similarity_cache_v10.csv")

    id_to_idx = dict(zip(rec["tmdb_id"], range(len(rec))))

    cache_groups = {
        source_id: group
        for source_id, group in cache.groupby(
            "source_tmdb_id", sort=False
        )
    }

    return {
        "rec": rec,
        "cache_groups": cache_groups,
        "id_to_idx": id_to_idx
    }


def get_recommendation_reason(rec, source_idx, target_idx):
    source = rec.iloc[source_idx]
    target = rec.iloc[target_idx]
    reasons = []

    source_genres = set(str(source["genres"]).split(", ")) - {""}
    target_genres = set(str(target["genres"]).split(", ")) - {""}
    common_genres = source_genres & target_genres

    if common_genres:
        reasons.append("Genres: " + ", ".join(sorted(common_genres)))

    if source["original_language"] == target["original_language"]:
        reasons.append("Same language")

    for column, label in [
        ("created_by", "Creator"),
        ("imdb_directors", "Director"),
        ("imdb_writers", "Writer")
    ]:
        source_names = set(str(source[column]).split(", ")) - {""}
        target_names = set(str(target[column]).split(", ")) - {""}
        common_names = source_names & target_names

        if common_names:
            reasons.append(
                label + ": " + ", ".join(sorted(common_names))
            )

    if not reasons:
        reasons.append("Similar content")

    return " | ".join(reasons)


def recommend_shows_v10(model, title=None, n=10, tmdb_id=None):
    rec = model["rec"]
    cache_groups = model["cache_groups"]
    id_to_idx = model["id_to_idx"]

    if tmdb_id is not None:
        idx = id_to_idx.get(tmdb_id)
        if idx is None:
            return f"TMDB ID '{tmdb_id}' not found."

    elif title is not None:
        matches = rec.index[
            rec["name"].str.lower() == title.lower().strip()
        ].tolist()

        if not matches:
            return f"'{title}' not found in dataset."

        idx = matches[0]

    else:
        return "Please provide either a title or tmdb_id."

    source = rec.iloc[idx]
    source_id = source["tmdb_id"]
    source_title = source["name"].lower()

    candidates = cache_groups.get(source_id)

    if candidates is None:
        return f"No cached recommendations found for TMDB ID {source_id}."

    candidates = candidates[
        candidates["target_tmdb_id"].isin(id_to_idx)
    ].copy()

    candidates["row_idx"] = candidates["target_tmdb_id"].map(id_to_idx)
    candidates = candidates[candidates["row_idx"].notna()].copy()
    candidates["row_idx"] = candidates["row_idx"].astype(int)

    target_rows = rec.iloc[candidates["row_idx"].to_numpy()]

    candidates = candidates[
        target_rows["name"].str.lower().to_numpy() != source_title
    ].copy()

    candidate_rows = rec.iloc[candidates["row_idx"].to_numpy()]

    candidates["recommendation_score"] = (
        candidates["content_similarity"].to_numpy() * 0.75
        + candidate_rows["quality_score"].to_numpy() * 0.15
        + candidate_rows["popularity_score"].to_numpy() * 0.10
    )

    candidates = candidates.sort_values(
        "recommendation_score", ascending=False
    ).head(max(0, n))

    indices = candidates["row_idx"].to_numpy()

    result = rec.iloc[indices][[
        "tmdb_id", "name", "genres", "original_language",
        "vote_average", "imdb_rating", "poster_path"
    ]].copy()

    result["content_similarity"] = (
        candidates["content_similarity"].round(4).to_numpy()
    )
    result["recommendation_score"] = (
        candidates["recommendation_score"].round(4).to_numpy()
    )
    result["reason"] = [
        get_recommendation_reason(rec, idx, target_idx)
        for target_idx in indices
    ]

    return result.reset_index(drop=True)
