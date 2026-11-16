
from django.shortcuts import render

from .tmdb import (
    search_multi,
    get_person_details,
    get_person_combined_credits,
)


def global_search(request):
    query = request.GET.get("q", "").strip()

    movies = []
    tv_shows = []
    people = []

    search_error = False
    current_page = 1
    total_pages = 0

    try:
        current_page = int(request.GET.get("page", 1))
    except (TypeError, ValueError):
        current_page = 1

    current_page = max(1, min(current_page, 500))

    if query:

        if len(query) > 150:
            search_error = True

        else:
            response = search_multi(
                query=query,
                page=current_page,
            )

            if not isinstance(response, dict):
                search_error = True

            else:
                total_pages = response.get("total_pages", 0)

                for item in response.get("results", []):

                    if not isinstance(item, dict):
                        continue

                    media_type = item.get("media_type")

                    if media_type == "movie":
                        movies.append(item)

                    elif media_type == "tv":
                        tv_shows.append(item)

                    elif media_type == "person":
                        people.append(item)

            # -----------------------------------------
            # PRIORITIZE EXACT PEOPLE MATCHES
            # -----------------------------------------

            people.sort(
                key=lambda person: (
                    person.get("name", "").casefold() != query.casefold(),
                    -(person.get("popularity") or 0),
                )
            )

            # -----------------------------------------
            # ADD EXACT PERSON'S DIRECTED MOVIES
            # -----------------------------------------

            exact_people = [
                person
                for person in people
                if person.get("name", "").casefold() == query.casefold()
            ]

            for person in exact_people:

                person_id = person.get("id")

                if not person_id:
                    continue

                credits = get_person_combined_credits(person_id)

                if not isinstance(credits, dict):
                    continue

                for credit in credits.get("crew", []):

                    if not isinstance(credit, dict):
                        continue

                    if (
                        credit.get("media_type") != "movie"
                        or credit.get("department") != "Directing"
                        or credit.get("job") != "Director"
                    ):
                        continue

                    movie = {
                        "id": credit.get("id"),
                        "title": credit.get("title"),
                        "poster_path": credit.get("poster_path"),
                        "release_date": credit.get("release_date"),
                        "vote_average": credit.get("vote_average"),
                        "overview": credit.get("overview"),
                        "media_type": "movie",
                        "popularity": credit.get("popularity", 0),
                    }

                    if movie["id"] and movie["title"]:
                        movies.append(movie)

            # -----------------------------------------
            # REMOVE DUPLICATE MOVIES
            # -----------------------------------------

            unique_movies = {}

            for movie in movies:

                movie_id = movie.get("id")

                if movie_id and movie_id not in unique_movies:
                    unique_movies[movie_id] = movie

            movies = list(unique_movies.values())

            movies.sort(
                key=lambda movie: (
                    -(movie.get("popularity") or 0),
                    movie.get("title", "").casefold(),
                )
            )

    context = {
        "query": query,
        "movies": movies,
        "tv_shows": tv_shows,
        "people": people,
        "search_error": search_error,
        "current_page": current_page,
        "total_pages": total_pages,
        "has_results": bool(movies or tv_shows or people),
    }

    return render(
        request,
        "search/global_search.html",
        context,
    )


# ==================================================
# PERSON DETAIL PAGE
# ==================================================

def person_detail(request, person_id):

    person = get_person_details(person_id)

    if not isinstance(person, dict):
        return render(
            request,
            "search/person_detail.html",
            {
                "person": None,
                "movies": [],
                "tv_shows": [],
                "person_error": True,
            },
        )

    credits = get_person_combined_credits(person_id)

    if not isinstance(credits, dict):
        credits = {}

    movie_credits = []
    tv_credits = []

    # -----------------------------------------
    # CAST CREDITS
    # -----------------------------------------

    for item in credits.get("cast", []):

        if not isinstance(item, dict):
            continue

        if item.get("media_type") == "movie":
            movie_credits.append(item)

        elif item.get("media_type") == "tv":
            tv_credits.append(item)

    # -----------------------------------------
    # CREW CREDITS
    # -----------------------------------------

    for item in credits.get("crew", []):

        if not isinstance(item, dict):
            continue

        if item.get("media_type") == "movie":
            movie_credits.append(item)

        elif item.get("media_type") == "tv":
            tv_credits.append(item)

    # -----------------------------------------
    # REMOVE DUPLICATE MOVIES
    # -----------------------------------------

    unique_movies = {}

    for item in movie_credits:

        item_id = item.get("id")

        if item_id and item_id not in unique_movies:
            unique_movies[item_id] = item

    movie_credits = list(unique_movies.values())

    # -----------------------------------------
    # REMOVE DUPLICATE TV SHOWS
    # -----------------------------------------

    unique_tv = {}

    for item in tv_credits:

        item_id = item.get("id")

        if item_id and item_id not in unique_tv:
            unique_tv[item_id] = item

    tv_credits = list(unique_tv.values())

    # -----------------------------------------
    # SORT BY RELEASE DATE
    # -----------------------------------------

    movie_credits.sort(
        key=lambda item: item.get("release_date") or "",
        reverse=True,
    )

    tv_credits.sort(
        key=lambda item: item.get("first_air_date") or "",
        reverse=True,
    )

    context = {
        "person": person,
        "movies": movie_credits,
        "tv_shows": tv_credits,
        "person_error": False,
    }

    return render(
        request,
        "search/person_detail.html",
        context,
    )
