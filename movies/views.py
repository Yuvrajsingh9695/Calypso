from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from comments.models import Comment
from .models import Movie
from tvshows.models import TVShow


# ==================================================
# HOME
# ==================================================


def home_page(request):

    # --------------------------------------------------
    # Latest Movies
    # --------------------------------------------------

    latest_movies = (
        Movie.objects.filter(
            vote_count__gte=10,
            release_date__isnull=False,
            poster_path__isnull=False,
        )
        .exclude(poster_path="")
        .order_by("-release_date")[:8]
    )

    # --------------------------------------------------
    # Popular Movies
    # --------------------------------------------------

    popular_movies = (
        Movie.objects.filter(
            vote_count__gte=10,
            poster_path__isnull=False,
        )
        .exclude(poster_path="")
        .order_by("-popularity")[:8]
    )

    # --------------------------------------------------
    # Latest TV Shows
    # --------------------------------------------------

    latest_shows = (
        TVShow.objects.filter(
            vote_count__gte=10,
            first_air_date__isnull=False,
            poster_path__isnull=False,
        )
        .exclude(poster_path="")
        .order_by("-first_air_date")[:8]
    )

    # --------------------------------------------------
    # Popular TV Shows
    # --------------------------------------------------

    popular_shows = (
        TVShow.objects.filter(
            vote_count__gte=10,
            poster_path__isnull=False,
        )
        .exclude(poster_path="")
        .order_by("-popularity")[:8]
    )

    # ==================================================
    # HOMEPAGE DISCOVERY TABS
    # ==================================================

    # --------------------------------------------------
    # Most Commented Movies
    #
    # Counts all comments belonging to each movie.
    # --------------------------------------------------

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
        .order_by(
            "-comment_count",
            "-vote_count",
        )[:8]
    )

    # --------------------------------------------------
    # Most Liked Movies
    #
    # Counts likes received by comments belonging
    # to each movie.
    # --------------------------------------------------

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

    # --------------------------------------------------
    # IMDb Top Rated Movies
    #
    # imdb_votes is included so that a movie with
    # an unusually high rating but almost no votes
    # does not dominate the section.
    # --------------------------------------------------

    imdb_top_movies = (
        Movie.objects.filter(
            vote_count__gte=10,
            poster_path__isnull=False,
            imdb_rating__isnull=False,
            imdb_rating__gt=0,
            imdb_votes__isnull=False,
            imdb_votes__gte=100,
        )
        .exclude(poster_path="")
        .order_by(
            "-imdb_rating",
            "-imdb_votes",
        )[:8]
    )

    # --------------------------------------------------
    # Render Homepage
    # --------------------------------------------------

    return render(
        request,
        "movies/index.html",
        {
            "latest_movies": latest_movies,
            "popular_movies": popular_movies,
            "latest_shows": latest_shows,
            "popular_shows": popular_shows,

            # Discovery tabs
            "most_commented_movies": most_commented_movies,
            "most_liked_movies": most_liked_movies,
            "imdb_top_movies": imdb_top_movies,
        },
    )


# ==================================================
# MOVIE LIST
# ==================================================


def movie_list(request, page=1):

    query = request.GET.get("q", "").strip()

    movies = Movie.objects.filter(
        vote_count__gte=10
    )

    if query:
        movies = movies.filter(
            Q(title__icontains=query)
        )

    paginator = Paginator(
        movies,
        24,
    )

    page_obj = paginator.get_page(page)

    return render(
        request,
        "movies/movie_api.html",
        {
            "movies": page_obj.object_list,
            "page_obj": page_obj,
            "page": page_obj.number,
            "total_pages": paginator.num_pages,
            "query": query,
        },
    )


# ==================================================
# MOVIE DETAIL
# ==================================================


def movie_detail(request, movie_id):

    movie = get_object_or_404(
        Movie,
        tmdb_id=movie_id,
    )

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

    return render(
        request,
        "movies/movie_detail.html",
        {
            "movie": movie,
            "comments": comments,
            "comment_form_url": reverse(
                "add_movie_comment",
                args=[movie.id],
            ),
        },
    )


# ==================================================
# GENRES
# ==================================================


def genre_movies(request, genre):

    movies = (
        Movie.objects.filter(
            genres__icontains=genre,
            vote_count__gte=10,
        )
        .order_by("-release_date")
    )

    paginator = Paginator(
        movies,
        24,
    )

    page_obj = paginator.get_page(
        request.GET.get("page", 1)
    )

    return render(
        request,
        "movies/movie_api.html",
        {
            "movies": page_obj.object_list,
            "page_obj": page_obj,
            "page": page_obj.number,
            "total_pages": paginator.num_pages,
            "query": "",
            "genre": genre,
        },
    )


# ==================================================
# OLD STATIC PAGES
# ==================================================


def movies2(request):
    return render(
        request,
        "movies/movies2.html",
    )


def movies3(request):
    return render(
        request,
        "movies/movies3.html",
    )


# ==================================================
# GENRE SHORTCUTS
# ==================================================


def action(request):
    return genre_movies(
        request,
        "Action",
    )


def horror(request):
    return genre_movies(
        request,
        "Horror",
    )


def drama(request):
    return genre_movies(
        request,
        "Drama",
    )


def scifi(request):
    return genre_movies(
        request,
        "Science Fiction",
    )


def romance(request):
    return genre_movies(
        request,
        "Romance",
    )


def thriller(request):
    return genre_movies(
        request,
        "Thriller",
    )


def comedy(request):
    return genre_movies(
        request,
        "Comedy",
    )


def animation(request):
    return genre_movies(
        request,
        "Animation",
    )