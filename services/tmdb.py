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


def get_tv_season_details(show_id, season_number):
    """
    Fetch all episode information for one TV season.
    """

    params = {
        "language": DEFAULT_LANGUAGE,
    }

    return tmdb_request(
        f"/tv/{show_id}/season/{season_number}",
        params=params,
    )


DEFAULT_LANGUAGE = "en-US"
DEFAULT_REGION = "IN"


def get_tv_episode_details(
    show_id,
    season_number,
    episode_number,
):
    """
    Fetch detailed information about an individual TV episode.
    """

    params = {
        "language": DEFAULT_LANGUAGE,
    }

    return tmdb_request(
        (f"/tv/{show_id}/season/{season_number}" f"/episode/{episode_number}"),
        params=params,
    )


def get_trending_movies(time_window="week", page=1):
    if time_window not in ("day", "week"):
        time_window = "week"

    params = {
        "language": DEFAULT_LANGUAGE,
        "page": page,
    }

    return tmdb_request(
        f"/trending/movie/{time_window}",
        params=params,
    )


def get_now_playing_movies(page=1, region=DEFAULT_REGION):
    params = {
        "language": DEFAULT_LANGUAGE,
        "page": page,
        "region": region,
    }

    return tmdb_request("/movie/now_playing", params=params)


def get_upcoming_movies(page=1, region=DEFAULT_REGION):
    params = {
        "language": DEFAULT_LANGUAGE,
        "page": page,
        "region": region,
    }

    return tmdb_request("/movie/upcoming", params=params)


def get_top_rated_movies(page=1):
    params = {
        "language": DEFAULT_LANGUAGE,
        "page": page,
    }

    return tmdb_request("/movie/top_rated", params=params)


# ==================================================
# TV SHOW DISCOVERY
# ==================================================


def get_popular_tv_shows(page=1):
    params = {
        "language": DEFAULT_LANGUAGE,
        "page": page,
    }

    return tmdb_request("/tv/popular", params=params)


def get_trending_tv_shows(time_window="week", page=1):
    if time_window not in ("day", "week"):
        time_window = "week"

    params = {
        "language": DEFAULT_LANGUAGE,
        "page": page,
    }

    return tmdb_request(
        f"/trending/tv/{time_window}",
        params=params,
    )


def get_airing_today_tv_shows(page=1):
    params = {
        "language": DEFAULT_LANGUAGE,
        "page": page,
    }

    return tmdb_request("/tv/airing_today", params=params)


def get_on_the_air_tv_shows(page=1):
    params = {
        "language": DEFAULT_LANGUAGE,
        "page": page,
    }

    return tmdb_request("/tv/on_the_air", params=params)


def get_top_rated_tv_shows(page=1):
    params = {
        "language": DEFAULT_LANGUAGE,
        "page": page,
    }

    return tmdb_request("/tv/top_rated", params=params)


# Replace discover_tv_shows() with this version.


def discover_tv_shows(
    page=1,
    genre=None,
    year=None,
    sort_by="popularity.desc",
    first_air_date_gte=None,
    first_air_date_lte=None,
    vote_count_gte=None,
    with_original_language=None,
    with_origin_country=None,
):
    params = {
        "language": DEFAULT_LANGUAGE,
        "page": page,
        "sort_by": sort_by,
        "include_adult": "false",
    }

    if genre:
        params["with_genres"] = genre

    if year:
        params["first_air_date_year"] = year

    if first_air_date_gte:
        params["first_air_date.gte"] = first_air_date_gte

    if first_air_date_lte:
        params["first_air_date.lte"] = first_air_date_lte

    if vote_count_gte is not None:
        params["vote_count.gte"] = vote_count_gte

    if with_original_language:
        params["with_original_language"] = with_original_language

    if with_origin_country:
        params["with_origin_country"] = with_origin_country

    return tmdb_request("/discover/tv", params=params)


# Replace discover_movies() with this version.


def discover_movies(
    page=1,
    genre=None,
    year=None,
    sort_by="popularity.desc",
    release_date_gte=None,
    release_date_lte=None,
    region=None,
    vote_count_gte=None,
):
    params = {
        "language": DEFAULT_LANGUAGE,
        "page": page,
        "sort_by": sort_by,
        "include_adult": "false",
        "include_video": "false",
    }

    if genre:
        params["with_genres"] = genre

    if year:
        params["primary_release_year"] = year

    if release_date_gte:
        params["primary_release_date.gte"] = release_date_gte

    if release_date_lte:
        params["primary_release_date.lte"] = release_date_lte

    if region:
        params["region"] = region

    if vote_count_gte is not None:
        params["vote_count.gte"] = vote_count_gte

    return tmdb_request("/discover/movie", params=params)


# ==================================================
# TV SHOW DETAILS AND CREDITS
# ==================================================


def get_tv_details(show_id):
    params = {
        "language": DEFAULT_LANGUAGE,
        "append_to_response": "videos,content_ratings,external_ids",
    }

    return tmdb_request(
        f"/tv/{show_id}",
        params=params,
    )


def get_tv_credits(show_id):
    params = {
        "language": DEFAULT_LANGUAGE,
    }

    return tmdb_request(
        f"/tv/{show_id}/credits",
        params=params,
    )


def get_similar_tv_shows(tv_id, page=1):
    params = {
        "language": DEFAULT_LANGUAGE,
        "page": page,
    }

    return tmdb_request(
        f"/tv/{tv_id}/similar",
        params=params,
    )


def get_recommended_tv_shows(tv_id, page=1):
    params = {
        "language": DEFAULT_LANGUAGE,
        "page": page,
    }

    return tmdb_request(
        f"/tv/{tv_id}/recommendations",
        params=params,
    )


def search_tv_shows(query, page=1):
    if not query or not query.strip():
        return None

    params = {
        "query": query.strip(),
        "language": DEFAULT_LANGUAGE,
        "page": page,
        "include_adult": "false",
    }

    return tmdb_request("/search/tv", params=params)


def get_recommended_movies(movie_id, page=1):
    params = {
        "language": DEFAULT_LANGUAGE,
        "page": page,
    }

    return tmdb_request(
        f"/movie/{movie_id}/recommendations",
        params=params,
    )


# ==================================================
# DISCOVER MOVIES
# ==================================================
def discover_movies(
    page=1,
    genre=None,
    year=None,
    sort_by="popularity.desc",
    release_date_gte=None,
    release_date_lte=None,
    region=None,
    vote_count_gte=None,
):
    params = {
        "language": DEFAULT_LANGUAGE,
        "page": page,
        "sort_by": sort_by,
        "include_adult": "false",
        "include_video": "false",
    }

    if genre:
        params["with_genres"] = genre

    if year:
        params["primary_release_year"] = year

    if release_date_gte:
        params["primary_release_date.gte"] = release_date_gte

    if release_date_lte:
        params["primary_release_date.lte"] = release_date_lte

    if region:
        params["region"] = region

    if vote_count_gte is not None:
        params["vote_count.gte"] = vote_count_gte

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
# GLOBAL SEARCH
# Movies + TV Shows + People
# ==================================================


def search_multi(query, page=1):

    if not query or not query.strip():
        return None

    params = {
        "query": query.strip(),
        "language": "en-US",
        "page": page,
        "include_adult": "false",
    }

    return tmdb_request("/search/multi", params=params)


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


# ==================================================
# PERSON / ACTOR DETAILS
# ==================================================


def get_person_details(person_id):

    params = {
        "language": "en-US",
    }

    return tmdb_request(f"/person/{person_id}", params=params)


# ==================================================
# PERSON MOVIE + TV CREDITS
# ==================================================


def get_person_combined_credits(person_id):

    params = {
        "language": "en-US",
    }

    return tmdb_request(f"/person/{person_id}/combined_credits", params=params)
