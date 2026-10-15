from functools import lru_cache
from pathlib import Path

from django.conf import settings

from .models import TVShow


RECOMMENDER_DIR = Path(settings.BASE_DIR) / "v10_cache"


@lru_cache(maxsize=1)
def get_v10_model():
    import importlib.util

    module_path = RECOMMENDER_DIR / "v10_recommender.py"

    if not module_path.exists():
        raise FileNotFoundError(
            f"V10 recommender module not found: {module_path}"
        )

    spec = importlib.util.spec_from_file_location(
        "calypso_v10_recommender",
        module_path,
    )

    if spec is None or spec.loader is None:
        raise ImportError("Could not load the V10 recommender module.")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    model = module.load_recommender(RECOMMENDER_DIR)

    return module, model


def get_similar_tv_shows(show, limit=10):
    module, model = get_v10_model()

    recommendations = module.recommend_shows_v10(
        model,
        tmdb_id=show.tmdb_id,
        n=limit,
    )

    # The recommender returns an error message instead of a DataFrame
    # when a show cannot be found.
    if not hasattr(recommendations, "columns"):
        return []

    recommended_ids = recommendations["tmdb_id"].tolist()

    # Fetch actual Django records so the template can link to each
    # show's existing detail page.
    database_shows = TVShow.objects.filter(
        tmdb_id__in=recommended_ids,
        is_adult=False,
        vote_count__gte=1000,
    )

    database_by_tmdb_id = {
        item.tmdb_id: item for item in database_shows
    }

    results = []

    for _, recommendation in recommendations.iterrows():
        recommended_show = database_by_tmdb_id.get(
            recommendation["tmdb_id"]
        )

        if recommended_show is None:
            continue

        # Apply the same content exclusions used by the TV views.
        blocked_terms = [
            "hentai", "ecchi", "porn", "pornographic",
            "sexually explicit", "explicit sexual",
            "adult animation", "adult anime", "erotic",
            "xxx", "sexual content", "sexual intercourse",
            "sex slave", "sex slavery", "incest", "nudity",
            "sexual violence",
        ]

        searchable_text = " ".join([
            recommended_show.name or "",
            recommended_show.original_name or "",
            recommended_show.overview or "",
            recommended_show.genres or "",
        ]).lower()

        if any(term in searchable_text for term in blocked_terms):
            continue

        results.append({
            "show": recommended_show,
            "reason": recommendation["reason"],
            "recommendation_score": recommendation[
                "recommendation_score"
            ],
            "poster_url": (
                "https://image.tmdb.org/t/p/w500"
                f"{recommendation['poster_path']}"
                if isinstance(recommendation["poster_path"], str)
                and recommendation["poster_path"].strip()
                else None
            ),
        })

    return results[:limit]