import time

import requests

from django.conf import settings

BASE_URL = "https://api.themoviedb.org/3"


def tmdb_request(endpoint, params=None, retries=4):
    """
    Send a request to TMDB with retry support.

    Returns:
        dict: TMDB response data when successful
        None: if all attempts fail
    """

    url = f"{BASE_URL}{endpoint}"

    headers = {
        "Authorization": f"Bearer {settings.TMDB_TOKEN}",
        "accept": "application/json",
        "User-Agent": "CalypsoMovieApp/1.0",
    }

    for attempt in range(1, retries + 1):

        try:
            response = requests.get(
                url,
                headers=headers,
                params=params,
                timeout=(10, 20),
            )

            response.raise_for_status()

            return response.json()

        except requests.RequestException as error:

            print(f"TMDB request failed " f"(attempt {attempt}/{retries}): {error}")

            if attempt < retries:

                wait_time = 2 ** (attempt - 1)

                print(f"Retrying TMDB request in " f"{wait_time} second(s)...")

                time.sleep(wait_time)

    print("TMDB request failed after all retry attempts.")

    return None


# ==================================================
# POPULAR MOVIES
# ==================================================


def get_popular_movies(page=1):

    params = {
        "language": "en-US",
        "page": page,
    }

    return tmdb_request("/movie/popular", params=params)


# ==================================================
# DISCOVER MOVIES
# ==================================================


def discover_movies(
    page=1,
    genre=None,
    year=None,
    sort_by="popularity.desc",
):

    params = {
        "language": "en-US",
        "page": page,
        "sort_by": sort_by,
        "include_adult": "false",
        "include_video": "false",
    }

    if genre:
        params["with_genres"] = genre

    if year:
        params["primary_release_year"] = year

    return tmdb_request("/discover/movie", params=params)


# ==================================================
# MOVIE DETAILS
# ==================================================


def get_movie_details(movie_id):

    params = {
        "language": "en-US",
    }

    return tmdb_request(f"/movie/{movie_id}", params=params)


# ==================================================
# SEARCH MOVIES
# ==================================================


def search_movies(query, page=1):

    if not query:
        return None

    params = {
        "query": query,
        "language": "en-US",
        "page": page,
        "include_adult": "false",
    }

    return tmdb_request("/search/movie", params=params)


# ==================================================
# MOVIE CREDITS
# ==================================================


def get_movie_credits(movie_id):

    params = {
        "language": "en-US",
    }

    return tmdb_request(f"/movie/{movie_id}/credits", params=params)


# ==================================================
# SIMILAR MOVIES
# ==================================================


def get_similar_movies(movie_id, page=1):

    params = {
        "language": "en-US",
        "page": page,
    }

    return tmdb_request(f"/movie/{movie_id}/similar", params=params)
