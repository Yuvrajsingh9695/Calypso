
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import Http404
from django.shortcuts import render
from django.urls import reverse

from comments.views import (
    get_comments_for_tv_scope,
    get_comments_for_tv_show,
)
from library.models import WatchlistItem
from services.tmdb import (
    get_tv_details,
    get_tv_credits,
    get_tv_season_details,
    get_tv_episode_details,
)
from .filters import clean_tv_queryset
from .models import TVShow
from .recommendations import get_similar_tv_shows




def sync_tv_show_record(show_id, show_data=None):
    """
    Keep a local TVShow record available for Calypso features
    that depend on the database (comments, watchlists, collections,
    and the V10 recommender), even when the show came directly from TMDB.
    """

    if show_data is None:
        show_data = get_tv_details(show_id)

    if not show_data:
        return TVShow.objects.filter(tmdb_id=show_id).first()

    defaults = {
        "name": show_data.get("name") or "Unknown",
        "overview": show_data.get("overview") or "",
        "poster_path": show_data.get("poster_path") or "",
        "backdrop_path": show_data.get("backdrop_path") or "",
        "first_air_date": show_data.get("first_air_date") or None,
        "last_air_date": show_data.get("last_air_date") or None,
        "vote_average": show_data.get("vote_average") or 0,
        "vote_count": show_data.get("vote_count") or 0,
        "popularity": show_data.get("popularity") or 0,
        "original_language": show_data.get("original_language") or "",
        "original_name": show_data.get("original_name") or "",
        "number_of_seasons": show_data.get("number_of_seasons") or 0,
        "number_of_episodes": show_data.get("number_of_episodes") or 0,
        "status": show_data.get("status") or "",
        "in_production": bool(show_data.get("in_production")),
        "genres": repr(show_data.get("genres") or []),
        "created_by": repr(show_data.get("created_by") or []),
        "origin_country": repr(show_data.get("origin_country") or []),
        "production_companies": repr(show_data.get("production_companies") or []),
        "tagline": show_data.get("tagline") or "",
        "is_adult": bool(show_data.get("adult", False)),
    }

    record, _ = TVShow.objects.update_or_create(
        tmdb_id=show_data.get("id", show_id),
        defaults=defaults,
    )

    return record


# ==================================================
# TV HOME
# ==================================================

def tv_home(request):

    base_queryset = clean_tv_queryset(
        TVShow.objects.filter(
            poster_path__isnull=False,
        ).exclude(poster_path="")
    )

    # LATEST TV SHOWS
    latest_shows = base_queryset.filter(
        first_air_date__isnull=False,
    ).order_by("-first_air_date")[:12]

    latest_ids = latest_shows.values_list(
        "tmdb_id",
        flat=True,
    )

    # TOP RATED TV SHOWS
    top_rated_shows = (
        base_queryset.exclude(
            tmdb_id__in=latest_ids,
        )
        .filter(vote_count__gte=40)
        .order_by(
            "-vote_average",
            "-vote_count",
        )[:12]
    )

    return render(
        request,
        "tvshows/index.html",
        {
            "latest_shows": latest_shows,
            "top_rated_shows": top_rated_shows,
        },
    )


# ==================================================
# TV LIST
# ==================================================

def tv_list(request, page=1):

    query = request.GET.get("q", "").strip()

    shows = clean_tv_queryset(TVShow.objects.all())

    if query:
        shows = shows.filter(
            Q(name__icontains=query)
            | Q(original_name__icontains=query)
        )

    shows = shows.order_by("-first_air_date")

    paginator = Paginator(shows, 24)
    page_obj = paginator.get_page(page)

    return render(
        request,
        "tvshows/tv_list.html",
        {
            "shows": page_obj.object_list,
            "page_obj": page_obj,
            "page": page_obj.number,
            "total_pages": paginator.num_pages,
            "query": query,
        },
    )


# ==================================================
# TV COUNTRY AND CERTIFICATION INFORMATION
# ==================================================

SPECIAL_COUNTRIES = {
    "US": "United States",
    "GB": "United Kingdom",
    "IN": "India",
}


def get_tv_release_information(show, content_ratings):
    """
    Return certifications for the show's origin countries,
    United States, United Kingdom and India.
    """

    if not show:
        return []

    country_names = {}

    for country in show.get("production_countries", []):
        code = country.get("iso_3166_1")
        name = country.get("name")

        if code and name:
            country_names[code] = name

    fallback_names = {
        "US": "United States",
        "GB": "United Kingdom",
        "IN": "India",
        "CA": "Canada",
        "AU": "Australia",
        "NZ": "New Zealand",
        "FR": "France",
        "DE": "Germany",
        "IT": "Italy",
        "ES": "Spain",
        "JP": "Japan",
        "KR": "South Korea",
        "CN": "China",
        "HK": "Hong Kong",
        "TW": "Taiwan",
        "RU": "Russia",
        "BR": "Brazil",
        "MX": "Mexico",
        "AR": "Argentina",
        "ZA": "South Africa",
        "NG": "Nigeria",
        "IE": "Ireland",
        "NL": "Netherlands",
        "SE": "Sweden",
        "NO": "Norway",
        "DK": "Denmark",
        "FI": "Finland",
        "CH": "Switzerland",
        "BE": "Belgium",
        "AT": "Austria",
        "PL": "Poland",
        "TR": "Turkey",
        "SG": "Singapore",
        "TH": "Thailand",
        "ID": "Indonesia",
        "MY": "Malaysia",
        "PH": "Philippines",
        "PK": "Pakistan",
        "BD": "Bangladesh",
        "AE": "United Arab Emirates",
        "SA": "Saudi Arabia",
        "EG": "Egypt",
        "IL": "Israel",
        "GR": "Greece",
        "PT": "Portugal",
        "IS": "Iceland",
        "LU": "Luxembourg",
        "CL": "Chile",
        "CO": "Colombia",
        "PE": "Peru",
        "VE": "Venezuela",
    }

    for code, name in fallback_names.items():
        country_names.setdefault(code, name)

    origin_codes = set(show.get("origin_country", []))

    allowed_codes = origin_codes | {"US", "GB", "IN"}

    ratings_by_country = {}

    for item in content_ratings:
        code = item.get("iso_3166_1")
        rating = item.get("rating")

        if code and rating:
            ratings_by_country[code] = rating

    release_information = []

    for code in allowed_codes:
        release_information.append(
            {
                "code": code,
                "country": (
                    country_names.get(code)
                    or SPECIAL_COUNTRIES.get(code)
                    or code
                ),
                "certification": ratings_by_country.get(code),
                "is_origin": code in origin_codes,
            }
        )

    priority = {"US": 0, "GB": 1, "IN": 2}

    release_information.sort(
        key=lambda item: (
            not item["is_origin"],
            priority.get(item["code"], 99),
            item["country"],
        )
    )

    return release_information


# ==================================================
# TV DETAIL
# TMDB API + LOCAL USER DATA + V10
# ==================================================

def tv_detail(request, show_id):

    # FETCH LIVE TV DETAILS FIRST.
    # A homepage result may not exist in the local dataset yet.
    show = get_tv_details(show_id)

    # Create/update the local record so comments, watchlists,
    # collections and V10 have a database object to work with.
    show_record = sync_tv_show_record(show_id, show)

    if not show_record:
        raise Http404("TV show not found")

    # HANDLE TMDB API FAILURE WHEN A LOCAL RECORD EXISTS.
    if not show:
        return render(
            request,
            "tvshows/tv_detail.html",
            {
                "api_error": True,
                "show_record": show_record,
            },
        )

    # CONTENT RATINGS
    content_ratings = show.get(
        "content_ratings",
        {},
    ).get(
        "results",
        [],
    )

    # RELEASE INFORMATION
    release_information = get_tv_release_information(
        show,
        content_ratings,
    )

    # FETCH CAST AND CREW
    credits = show.get("credits") or {}

    if not credits:
        credits = get_tv_credits(show_id) or {}

    cast_members = credits.get("cast", [])[:20]
    crew_members = credits.get("crew", [])

    aggregate_credits = show.get("aggregate_credits") or {}

    aggregate_cast = aggregate_credits.get("cast", [])
    aggregate_crew = aggregate_credits.get("crew", [])

    # FIND YOUTUBE TRAILER
    videos = show.get(
        "videos",
        {},
    ).get(
        "results",
        [],
    )

    trailer = next(
        (
            video
            for video in videos
            if (
                video.get("site") == "YouTube"
                and video.get("type") == "Trailer"
                and video.get("official", False)
                and video.get("key")
            )
        ),
        None,
    )

    if not trailer:
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

    trailer_url = None

    if trailer:
        trailer_url = (
            f"https://www.youtube.com/watch?v={trailer['key']}"
        )

    # SEASON INFORMATION
    seasons = show.get("seasons", [])

    # Prefer the season of the next episode; otherwise use the
    # season of the most recently aired episode.
    next_episode = show.get("next_episode_to_air") or {}
    last_episode = show.get("last_episode_to_air") or {}

    current_season_number = (
        next_episode.get("season_number")
        or last_episode.get("season_number")
    )

    # CERTIFICATION
    certification = next(
        (
            item.get("rating")
            for item in content_ratings
            if (
                item.get("iso_3166_1") == "IN"
                and item.get("rating")
            )
        ),
        None,
    )

    if not certification:
        certification = next(
            (
                item.get("rating")
                for item in content_ratings
                if (
                    item.get("iso_3166_1") == "US"
                    and item.get("rating")
                )
            ),
            None,
        )

    # ADDITIONAL TMDB METADATA
    external_ids = show.get("external_ids", {})

    keywords_data = show.get("keywords", {})
    keywords = keywords_data.get("results", [])

    images = show.get("images", {})
    backdrops = images.get("backdrops", [])
    posters = images.get("posters", [])

    # GENERAL TV SHOW COMMENTS ONLY
    # Season and episode comments are displayed separately.
    comments = get_comments_for_tv_show(show_record)

    # WATCHLIST
    in_watchlist = False

    if request.user.is_authenticated:
        in_watchlist = WatchlistItem.objects.filter(
            watchlist__user=request.user,
            tv_show=show_record,
        ).exists()

    # V10 SIMILAR TV SHOW RECOMMENDATIONS
    try:
        similar_shows = get_similar_tv_shows(
            show_record,
            limit=10,
        )

    except (
        FileNotFoundError,
        ImportError,
        OSError,
        ValueError,
    ):
        similar_shows = []

    # CONTEXT
    context = {
        "show": show,
        "show_record": show_record,

        # Cast and crew
        "credits": credits,
        "cast_members": cast_members,
        "crew_members": crew_members,

        # Aggregate credits
        "aggregate_credits": aggregate_credits,
        "aggregate_cast": aggregate_cast,
        "aggregate_crew": aggregate_crew,

        # Videos and trailer
        "videos": videos,
        "trailer": trailer,
        "trailer_url": trailer_url,

        # Seasons
        "seasons": seasons,
        "current_season_number": current_season_number,

        # Content ratings
        "content_ratings": content_ratings,
        "certification": certification,
        "release_information": release_information,

        # External IDs and keywords
        "external_ids": external_ids,
        "keywords": keywords,

        # Images
        "images": images,
        "backdrops": backdrops,
        "posters": posters,

        # User functionality
        "comments": comments,
        "comment_form_url": reverse(
            "add_tv_comment",
            args=[show_record.id],
        ),
        "in_watchlist": in_watchlist,

        # V10 recommendations
        "similar_shows": similar_shows,
    }

    return render(
        request,
        "tvshows/tv_detail.html",
        context,
    )


# ==================================================
# TV SEASON DETAIL
# ==================================================

def tv_season_detail(request, show_id, season_number):

    # Ensure the TV show exists locally, even if it was first
    # discovered through a live TMDB result.
    show_record = sync_tv_show_record(show_id)

    if not show_record:
        raise Http404("TV show not found")

    # FETCH SEASON AND EPISODE DETAILS FROM TMDB
    season = get_tv_season_details(
        show_id,
        season_number,
    )

    # HANDLE API FAILURE
    if not season:
        return render(
            request,
            "tvshows/tv_season_detail.html",
            {
                "api_error": True,
                "show_record": show_record,
                "season_number": season_number,
            },
        )

    # EPISODES
    episodes = season.get("episodes", [])

    # SEASON COMMENTS ONLY
    comments = get_comments_for_tv_scope(
        tv_show=show_record,
        season_number=season_number,
        episode_number=None,
    )

    comment_form_url = reverse(
        "add_tv_season_comment",
        kwargs={
            "tv_show_id": show_record.id,
            "season_number": season_number,
        },
    )

    # CONTEXT
    context = {
        "show_record": show_record,
        "season": season,
        "season_number": season_number,
        "episodes": episodes,
        "comments": comments,
        "comment_form_url": comment_form_url,
    }

    return render(
        request,
        "tvshows/tv_season_detail.html",
        context,
    )


# ==================================================
# TV EPISODE DETAIL
# ==================================================

def tv_episode_detail(request, show_id, season_number, episode_number):

    # Ensure the TV show exists locally, even if it was first
    # discovered through a live TMDB result.
    show_record = sync_tv_show_record(show_id)

    if not show_record:
        raise Http404("TV show not found")

    # FETCH EPISODE DETAILS
    episode = get_tv_episode_details(
        show_id,
        season_number,
        episode_number,
    )

    # FETCH SEASON INFORMATION
    # Used to determine previous and next episodes.
    season = get_tv_season_details(
        show_id,
        season_number,
    )

    # HANDLE TMDB API FAILURE
    if not episode or not season:
        return render(
            request,
            "tvshows/tv_episode_detail.html",
            {
                "api_error": True,
                "show_record": show_record,
                "season_number": season_number,
                "episode_number": episode_number,
            },
        )

    # EPISODE LIST AND NAVIGATION
    episodes = season.get("episodes", [])

    current_index = next(
        (
            index
            for index, item in enumerate(episodes)
            if item.get("episode_number") == episode_number
        ),
        None,
    )

    previous_episode = None
    next_episode = None

    if current_index is not None:

        if current_index > 0:
            previous_episode = episodes[current_index - 1]

        if current_index < len(episodes) - 1:
            next_episode = episodes[current_index + 1]

    # GUEST STARS AND CREW
    guest_stars = episode.get("guest_stars", [])
    crew_members = episode.get("crew", [])

    # EPISODE COMMENTS ONLY
    comments = get_comments_for_tv_scope(
        tv_show=show_record,
        season_number=season_number,
        episode_number=episode_number,
    )

    comment_form_url = reverse(
        "add_tv_episode_comment",
        kwargs={
            "tv_show_id": show_record.id,
            "season_number": season_number,
            "episode_number": episode_number,
        },
    )

    # CONTEXT
    context = {
        "show_record": show_record,
        "season": season,
        "episode": episode,

        "season_number": season_number,
        "episode_number": episode_number,

        "guest_stars": guest_stars,
        "crew_members": crew_members,

        "previous_episode": previous_episode,
        "next_episode": next_episode,

        "comments": comments,
        "comment_form_url": comment_form_url,
    }

    return render(
        request,
        "tvshows/tv_episode_detail.html",
        context,
    )


# ==================================================
# GENRE SHOWS
# ==================================================

def genre_shows(request, genre):

    shows = clean_tv_queryset(
        TVShow.objects.filter(
            genres__icontains=genre,
        )
    ).order_by("-first_air_date")

    paginator = Paginator(shows, 24)

    page_obj = paginator.get_page(
        request.GET.get("page", 1)
    )

    return render(
        request,
        "tvshows/tv_list.html",
        {
            "shows": page_obj.object_list,
            "page_obj": page_obj,
            "page": page_obj.number,
            "total_pages": paginator.num_pages,
            "query": "",
            "genre": genre,
        },
    )
