from datetime import timedelta

from django.core.paginator import Paginator
from django.db.models import Count
from django.http import Http404
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone

from comments.models import Comment
from library.models import WatchlistItem
from services.tmdb import (
    get_movie_details,
    get_movie_credits,
    get_person_details,
    get_person_combined_credits,
    get_popular_movies,
    get_now_playing_movies,
    get_upcoming_movies,
    search_movies,
    discover_movies,
    get_popular_tv_shows,
    get_top_rated_tv_shows,
    discover_tv_shows,
)
from tvshows.models import TVShow

from .models import Movie

TMDB_MOVIE_GENRES = {
    "Action": 28,
    "Animation": 16,
    "Horror": 27,
    "Thriller": 53,
    "Comedy": 35,
    "Science Fiction": 878,
    "Drama": 18,
    "Romance": 10749,
}


# ==================================================
# HOME
# ==================================================

def home_page(request):

    today = timezone.localdate()
    tomorrow = today + timedelta(days=1)

    # ==================================================
    # MOVIES
    # ==================================================

    latest_movies = (
        Movie.objects.filter(
            vote_count__gte=10,
            release_date__isnull=False,
            poster_path__isnull=False,
        )
        .exclude(poster_path="")
        .order_by("-release_date")[:8]
    )

    popular_movies = (
        Movie.objects.filter(
            vote_count__gte=10,
            poster_path__isnull=False,
        )
        .exclude(poster_path="")
        .order_by("-popularity")[:8]
    )

    # These two sections must use live TMDB results.
    # Local is_now_playing flags become stale and should not
    # decide whether a movie is currently in cinemas.
    now_playing_data = get_now_playing_movies(
        page=1,
        region="IN",
    ) or {}

    now_playing_movies = [
        movie for movie in now_playing_data.get("results", [])
        if movie.get("poster_path")
        and movie.get("release_date")
        and movie.get("release_date") <= today.isoformat()
    ][:8]

    upcoming_data = get_upcoming_movies(
        page=1,
        region="IN",
    ) or {}

    upcoming_movies = [
        movie for movie in upcoming_data.get("results", [])
        if movie.get("poster_path")
        and movie.get("release_date")
        and movie.get("release_date") > today.isoformat()
    ]

    # Fallback to Discover if the regional Upcoming endpoint
    # returns no future-dated results.
    if not upcoming_movies:
        upcoming_data = discover_movies(
            page=1,
            sort_by="primary_release_date.asc",
            release_date_gte=tomorrow.isoformat(),
            region="IN",
            vote_count_gte=0,
        ) or {}

        upcoming_movies = [
            movie for movie in upcoming_data.get("results", [])
            if movie.get("poster_path")
            and movie.get("release_date")
            and movie.get("release_date") > today.isoformat()
        ]

    upcoming_movies = upcoming_movies[:8]

    # ==================================================
    # TV SHOWS FROM TMDB API
    # ==================================================

    latest_data = discover_tv_shows(
        page=1,
        sort_by="first_air_date.desc",
        first_air_date_lte=today.isoformat(),
        vote_count_gte=10,
    ) or {}

    latest_shows = [
        show for show in latest_data.get("results", [])
        if show.get("poster_path") and show.get("first_air_date")
    ][:8]

    # Upcoming shows are filtered to English-language productions
    # from the US, UK and India, then ranked by popularity.
    # This avoids filling the section with low-visibility results
    # from unrelated markets.
    upcoming_data = discover_tv_shows(
        page=1,
        sort_by="popularity.desc",
        first_air_date_gte=tomorrow.isoformat(),
        vote_count_gte=0,
        with_original_language="en",
        with_origin_country="US|GB|IN",
    ) or {}

    upcoming_shows = [
        show for show in upcoming_data.get("results", [])
        if (
            show.get("poster_path")
            and show.get("first_air_date")
            and show.get("first_air_date") > today.isoformat()
        )
    ][:8]

    popular_data = get_popular_tv_shows(page=1) or {}
    popular_shows = [
        show for show in popular_data.get("results", [])
        if show.get("poster_path")
    ][:8]

    top_rated_data = get_top_rated_tv_shows(page=1) or {}
    top_rated_shows = [
        show for show in top_rated_data.get("results", [])
        if show.get("poster_path")
    ][:8]

    # ==================================================
    # MOVIE DISCOVERY TABS
    # ==================================================

    most_commented_movies = (
        Movie.objects.filter(
            vote_count__gte=10,
            poster_path__isnull=False,
        )
        .exclude(poster_path="")
        .annotate(
            comment_count=Count(
                "comments",
                distinct=True,
            )
        )
        .filter(comment_count__gt=0)
        .order_by("-comment_count", "-vote_count")[:8]
    )

    most_liked_movies = (
        Movie.objects.filter(
            vote_count__gte=10,
            poster_path__isnull=False,
        )
        .exclude(poster_path="")
        .annotate(
            like_count=Count(
                "comments__likes",
                distinct=True,
            ),
            comment_count=Count(
                "comments",
                distinct=True,
            ),
        )
        .filter(like_count__gt=0)
        .order_by(
            "-like_count",
            "-comment_count",
            "-vote_count",
        )[:8]
    )

    imdb_top_movies = (
        Movie.objects.filter(
            vote_count__gte=10,
            poster_path__isnull=False,
            imdb_rating__gt=0,
            imdb_votes__gte=100,
        )
        .exclude(poster_path="")
        .order_by("-imdb_rating", "-imdb_votes")[:8]
    )

    return render(
        request,
        "movies/index.html",
        {
            "latest_movies": latest_movies,
            "popular_movies": popular_movies,
            "upcoming_movies": upcoming_movies,
            "now_playing_movies": now_playing_movies,

            "latest_shows": latest_shows,
            "upcoming_shows": upcoming_shows,
            "popular_shows": popular_shows,
            "top_rated_shows": top_rated_shows,

            "most_commented_movies": most_commented_movies,
            "most_liked_movies": most_liked_movies,
            "imdb_top_movies": imdb_top_movies,
        },
    )


# ==================================================
# MOVIE LIST
# LIVE TMDB RESULTS
# ==================================================


def movie_list(request, page=1):

    query = request.GET.get("q", "").strip()

    if query:
        data = search_movies(query, page=page)
        title = "Search Results"
        description = f"Movies matching '{query}'."

    else:
        data = get_popular_movies(page=page)
        title = "Discover Movies"
        description = "Explore popular movies from TMDB."

    return render_tmdb_movie_page(
        request,
        data,
        page_title=title,
        page_description=description,
        pagination_url_name="movie-list-page",
        query=query,
        current_page=page,
    )


# ==================================================
# UPCOMING MOVIES
# LIVE TMDB RESULTS
# ==================================================


def upcoming_movies(request, page=1):

    data = get_upcoming_movies(
        page=page,
        region="IN",
    )

    return render_tmdb_movie_page(
        request,
        data,
        page_title="Upcoming Movies",
        page_description="Discover upcoming movie releases in India.",
        pagination_url_name="upcoming-movies-page",
        current_page=page,
    )


# ==================================================
# NEW RELEASES
# LAST 90 DAYS
# ==================================================


def new_releases(request, page=1):

    today = timezone.localdate()
    start_date = today - timedelta(days=90)

    data = discover_movies(
        page=page,
        sort_by="primary_release_date.desc",
        release_date_gte=start_date.isoformat(),
        release_date_lte=today.isoformat(),
        region="IN",
        vote_count_gte=10,
    )

    return render_tmdb_movie_page(
        request,
        data,
        page_title="New Releases",
        page_description="Explore movies released in the last 90 days.",
        pagination_url_name="new-releases-page",
        current_page=page,
    )


# ==================================================
# GENRE MOVIES
# LIVE TMDB RESULTS
# ==================================================


def genre_movies(request, genre):

    genre_id = TMDB_MOVIE_GENRES.get(genre)

    if not genre_id:
        return render_tmdb_movie_page(
            request,
            None,
            page_title=f"{genre} Movies",
            page_description="Genre not found.",
            genre=genre,
            pagination_query_mode=True,
        )

    page = request.GET.get("page", "1")

    try:
        page = max(1, min(int(page), 500))
    except (TypeError, ValueError):
        page = 1

    data = discover_movies(
        page=page,
        genre=genre_id,
        sort_by="popularity.desc",
        vote_count_gte=10,
    )

    return render_tmdb_movie_page(
        request,
        data,
        page_title=f"{genre} Movies",
        page_description=f"Explore popular {genre.lower()} movies.",
        genre=genre,
        pagination_query_mode=True,
        current_page=page,
    )


# ==================================================
# MOVIE DETAIL
# TMDB API + LOCAL USER DATA
# ==================================================


# ==================================================
# RELEASE INFORMATION HELPERS
# ==================================================

SPECIAL_RELEASE_COUNTRIES = {
    "US": "United States",
    "GB": "United Kingdom",
    "IN": "India",
}


def get_movie_release_information(tmdb_movie):
    """
    Return release information for:
    - Movie production/origin countries
    - United States
    - United Kingdom
    - India

    Prefer theatrical release (type 3).
    Fall back to limited theatrical release (type 2).
    """

    if not tmdb_movie:
        return []

    production_countries = tmdb_movie.get("production_countries", [])

    origin_countries = {}

    for country in production_countries:
        code = country.get("iso_3166_1")
        name = country.get("name")

        if code and name:
            origin_countries[code] = name

    # Include origin countries and the three requested regions.
    allowed_countries = dict(origin_countries)

    for code, name in SPECIAL_RELEASE_COUNTRIES.items():
        allowed_countries.setdefault(code, name)

    release_results = tmdb_movie.get("release_dates", {}).get("results", [])

    release_information = []

    for country in release_results:

        country_code = country.get("iso_3166_1")

        if country_code not in allowed_countries:
            continue

        country_name = allowed_countries[country_code]

        releases = country.get("release_dates", [])

        # Prefer theatrical releases.
        theatrical_releases = [
            release for release in releases if release.get("type") == 3
        ]

        # Fall back to limited theatrical releases.
        limited_releases = [release for release in releases if release.get("type") == 2]

        selected_releases = theatrical_releases or limited_releases or releases

        selected_releases = sorted(
            selected_releases,
            key=lambda item: item.get("release_date", ""),
        )

        if not selected_releases:
            continue

        selected = selected_releases[0]

        release_date = selected.get("release_date", "")
        certification = selected.get("certification") or "Not rated"

        release_information.append(
            {
                "code": country_code,
                "country": country_name,
                "release_date": release_date[:10] if release_date else "",
                "certification": certification,
                "release_type": selected.get("type"),
                "is_origin": country_code in origin_countries,
            }
        )

    # Put origin countries first, followed by US, UK and India.
    release_information.sort(
        key=lambda item: (
            not item["is_origin"],
            (
                ["US", "GB", "IN"].index(item["code"])
                if item["code"] in ["US", "GB", "IN"]
                else 0
            ),
            item["country"],
        )
    )

    return release_information


def movie_detail(request, movie_id):

    # --------------------------------------------------
    # FETCH MOVIE DETAILS FROM TMDB
    # --------------------------------------------------

    # The updated get_movie_details() function uses
    # append_to_response to retrieve additional metadata:
    #
    # credits
    # videos
    # release_dates
    # keywords
    # external_ids
    # images
    #
    # This avoids making multiple separate API requests.

    tmdb_movie = get_movie_details(movie_id)

    # --------------------------------------------------
    # GET LOCAL MOVIE RECORD
    # --------------------------------------------------

    movie = Movie.objects.filter(
        tmdb_id=movie_id,
    ).first()

    # If TMDB fails and the movie does not exist locally,
    # there is no record available to display.

    if not tmdb_movie and movie is None:
        raise Http404("Movie not found")

    # --------------------------------------------------
    # CREATE LOCAL MOVIE IF IT DOES NOT EXIST
    # --------------------------------------------------

    if movie is None:

        genres = ", ".join(
            genre.get("name", "")
            for genre in tmdb_movie.get("genres", [])
            if genre.get("name")
        )

        movie = Movie.objects.create(
            tmdb_id=tmdb_movie.get("id", movie_id),
            title=tmdb_movie.get("title", "Unknown"),
            overview=tmdb_movie.get("overview", ""),
            poster_path=tmdb_movie.get("poster_path") or "",
            backdrop_path=tmdb_movie.get("backdrop_path") or "",
            release_date=tmdb_movie.get("release_date") or None,
            runtime=tmdb_movie.get("runtime") or 0,
            original_language=tmdb_movie.get("original_language", ""),
            genres=genres,
            vote_average=tmdb_movie.get("vote_average") or 0,
            vote_count=tmdb_movie.get("vote_count") or 0,
            popularity=tmdb_movie.get("popularity") or 0,
        )

    # --------------------------------------------------
    # UPDATE LOCAL MOVIE METADATA FROM TMDB
    # --------------------------------------------------

    # The local Movie record is still required for:
    #
    # - Comments
    # - Watchlist
    # - Collections
    # - Likes and other user-related features
    #
    # However, TMDB remains the source of movie metadata.
    # Updating these fields prevents old local metadata
    # from being displayed when fresh TMDB data exists.

    if tmdb_movie:

        genres = ", ".join(
            genre.get("name", "")
            for genre in tmdb_movie.get("genres", [])
            if genre.get("name")
        )

        metadata = {
            "title": tmdb_movie.get("title") or movie.title,
            "overview": tmdb_movie.get("overview") or "",
            "poster_path": tmdb_movie.get("poster_path") or "",
            "backdrop_path": tmdb_movie.get("backdrop_path") or "",
            "release_date": tmdb_movie.get("release_date") or None,
            "runtime": tmdb_movie.get("runtime") or 0,
            "original_language": (
                tmdb_movie.get("original_language") or movie.original_language
            ),
            "genres": genres,
            "vote_average": tmdb_movie.get("vote_average") or 0,
            "vote_count": tmdb_movie.get("vote_count") or 0,
            "popularity": tmdb_movie.get("popularity") or 0,
        }

        fields_to_update = []

        for field, value in metadata.items():

            if getattr(movie, field) != value:
                setattr(movie, field, value)
                fields_to_update.append(field)

        if fields_to_update:
            movie.save(update_fields=fields_to_update)

    # --------------------------------------------------
    # FETCH CAST AND CREW FROM TMDB
    # --------------------------------------------------

    credits = {}

    if tmdb_movie:
        credits = tmdb_movie.get("credits") or {}

    # Fallback for responses that do not contain credits.
    # This also supports older or incomplete API responses.

    if not credits:
        credits = get_movie_credits(movie_id) or {}

    cast_members = credits.get("cast", [])
    crew_members = credits.get("crew", [])

    # --------------------------------------------------
    # CAST NAMES
    # --------------------------------------------------

    cast_names = ", ".join(
        person.get("name", "") for person in cast_members[:15] if person.get("name")
    )

    # --------------------------------------------------
    # DIRECTOR NAMES
    # --------------------------------------------------

    director_names = ", ".join(
        person.get("name", "")
        for person in crew_members
        if (person.get("job") == "Director" and person.get("name"))
    )

    # --------------------------------------------------
    # WRITER NAMES
    # --------------------------------------------------

    writer_names = ", ".join(
        person.get("name", "")
        for person in crew_members
        if (
            person.get("job")
            in [
                "Writer",
                "Screenplay",
                "Story",
            ]
            and person.get("name")
        )
    )

    # Keep the local cast, director and writer fields
    # synchronized for other parts of the application.

    fields_to_update = []

    if cast_names and movie.cast != cast_names:
        movie.cast = cast_names
        fields_to_update.append("cast")

    if director_names and movie.director != director_names:
        movie.director = director_names
        fields_to_update.append("director")

    if writer_names and movie.writers != writer_names:
        movie.writers = writer_names
        fields_to_update.append("writers")

    if fields_to_update:
        movie.save(update_fields=fields_to_update)

    # --------------------------------------------------
    # ADDITIONAL TMDB METADATA
    # --------------------------------------------------

    videos = tmdb_movie.get("videos", {}).get("results", []) if tmdb_movie else []

    release_dates = (
        tmdb_movie.get("release_dates", {}).get("results", []) if tmdb_movie else []
    )

    keywords_data = tmdb_movie.get("keywords", {}) if tmdb_movie else {}

    keywords = keywords_data.get("keywords", [])

    external_ids = tmdb_movie.get("external_ids", {}) if tmdb_movie else {}

    images = tmdb_movie.get("images", {}) if tmdb_movie else {}

    # --------------------------------------------------
    # YOUTUBE TRAILER
    # --------------------------------------------------

    trailer = next(
        (
            video
            for video in videos
            if (
                video.get("site") == "YouTube"
                and video.get("type") == "Trailer"
                and video.get("key")
            )
        ),
        None,
    )

    # --------------------------------------------------
    # CHECK WATCHLIST
    # --------------------------------------------------

    in_watchlist = False

    if request.user.is_authenticated:

        in_watchlist = WatchlistItem.objects.filter(
            watchlist__user=request.user,
            movie=movie,
        ).exists()

    # --------------------------------------------------
    # FETCH COMMENTS
    # --------------------------------------------------

    comments = (
        Comment.objects.filter(
            movie=movie,
            parent__isnull=True,
        )
        .select_related("user")
        .prefetch_related(
            "replies__user",
            "likes",
        )
    )
    release_information = get_movie_release_information(tmdb_movie)
    # --------------------------------------------------
    # RENDER PAGE
    # --------------------------------------------------

    return render(
        request,
        "movies/movie_detail.html",
        {
            # Local movie object.
            # Used by comments, watchlist and other
            # database-related functionality.
            "movie": movie,
            # Fresh TMDB response.
            "tmdb_movie": tmdb_movie,
            # Cast and crew.
            "cast_members": cast_members,
            "crew_members": crew_members,
            "credits": credits,
            # Additional TMDB information.
            "videos": videos,
            "trailer": trailer,
            "release_dates": release_dates,
            "keywords": keywords,
            "external_ids": external_ids,
            "images": images,
            # User-related information.
            "comments": comments,
            "in_watchlist": in_watchlist,
            "release_information": release_information,
            "comment_form_url": reverse(
                "add_movie_comment",
                args=[movie.id],
            ),
        },
    )


# ==================================================
# GENRE SHORTCUTS
# ==================================================


def action(request):
    return genre_movies(request, "Action")


def horror(request):
    return genre_movies(request, "Horror")


def drama(request):
    return genre_movies(request, "Drama")


def scifi(request):
    return genre_movies(request, "Science Fiction")


def romance(request):
    return genre_movies(request, "Romance")


def thriller(request):
    return genre_movies(request, "Thriller")


def comedy(request):
    return genre_movies(request, "Comedy")


def animation(request):
    return genre_movies(request, "Animation")


def genres_page(request):

    return render(
        request,
        "movies/genres.html",
    )


# ==================================================
# NOW PLAYING
# ==================================================


def now_playing(request, page=1):

    data = get_now_playing_movies(
        page=page,
        region="IN",
    )

    return render_tmdb_movie_page(
        request,
        data,
        page_title="Now Playing",
        page_description="Discover movies currently playing in theatres in India.",
        pagination_url_name="now-playing-page",
        current_page=page,
    )


# ==================================================
# TMDB MOVIE PAGE RENDERER
# ==================================================


def render_tmdb_movie_page(
    request,
    data,
    page_title="Discover Movies",
    page_description="Explore movies from TMDB.",
    pagination_url_name="movie-list-page",
    query="",
    genre=None,
    pagination_query_mode=False,
    current_page=1,
):
    """
    Render a paginated movie listing using TMDB API results.
    """

    # Handle failed TMDB requests safely.
    data = data or {}

    movies = data.get("results", [])

    # TMDB supports a maximum of 500 accessible pages.
    total_pages = min(data.get("total_pages", 1), 500)

    # Use the page number returned by TMDB.
    # Fall back to the requested page if unavailable.
    current_page = data.get("page", current_page)

    return render(
        request,
        "movies/movie_api.html",
        {
            "movies": movies,
            "page": current_page,
            "total_pages": total_pages,
            "query": query,
            "genre": genre,
            "page_title": page_title,
            "page_description": page_description,
            "pagination_url_name": pagination_url_name,
            "pagination_query_mode": pagination_query_mode,
        },
    )


# ==================================================
# ACTOR / PERSON DETAIL
# ==================================================


def person_detail(request, person_id):

    # --------------------------------------------------
    # GET ACTOR DETAILS
    # --------------------------------------------------

    person = get_person_details(person_id)

    if not person:
        raise Http404("Person not found")

    # --------------------------------------------------
    # GET COMBINED MOVIE AND TV CREDITS
    # --------------------------------------------------

    credits = get_person_combined_credits(person_id) or {}

    # --------------------------------------------------
    # MOVIE CREDITS
    # --------------------------------------------------

    movies = [
        item for item in credits.get("cast", []) if item.get("media_type") == "movie"
    ]

    # Sort movies by release date, newest first.
    movies.sort(
        key=lambda movie: movie.get("release_date") or "",
        reverse=True,
    )

    # --------------------------------------------------
    # TV SHOW CREDITS
    # --------------------------------------------------

    tv_shows = [
        item for item in credits.get("cast", []) if item.get("media_type") == "tv"
    ]

    # Sort TV shows by first air date, newest first.
    tv_shows.sort(
        key=lambda show: show.get("first_air_date") or "",
        reverse=True,
    )

    # --------------------------------------------------
    # LIMIT RESULTS
    # --------------------------------------------------

    movies = movies[:60]
    tv_shows = tv_shows[:60]

    # --------------------------------------------------
    # CONTEXT
    # --------------------------------------------------

    context = {
        "person": person,
        "movies": movies,
        "tv_shows": tv_shows,
    }

    return render(
        request,
        "movies/person_detail.html",
        context,
    )
