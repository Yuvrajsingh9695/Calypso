from django.urls import path
from . import views

urlpatterns = [
    # HOME
    path("", views.home_page, name="home"),
    # MOVIE LIST
    path("movies/", views.movie_list, name="movies"),
    path("movies/page/<int:page>/", views.movie_list, name="movie-list-page"),
    # UPCOMING MOVIES
    path("movies/upcoming/", views.upcoming_movies, name="upcoming-movies"),
    path(
        "movies/upcoming/page/<int:page>/",
        views.upcoming_movies,
        name="upcoming-movies-page",
    ),
    # NEW RELEASES
    path("movies/new-releases/", views.new_releases, name="new-releases"),
    path(
        "movies/new-releases/page/<int:page>/",
        views.new_releases,
        name="new-releases-page",
    ),
    # GENRES
    path("genre/action/", views.action, name="action"),
    path("genre/animation/", views.animation, name="animation"),
    path("genre/horror/", views.horror, name="horror"),
    path("genre/thriller/", views.thriller, name="thriller"),
    path("genre/comedy/", views.comedy, name="comedy"),
    path("genre/scifi/", views.scifi, name="scifi"),
    path("genre/drama/", views.drama, name="drama"),
    path("genre/romance/", views.romance, name="romance"),
    path("genres/", views.genres_page, name="genres-page"),
    # NOW PLAYING MOVIES
    path(
        "movies/now-playing/",
        views.now_playing,
        name="now-playing",
    ),
    path(
        "movies/now-playing/page/<int:page>/",
        views.now_playing,
        name="now-playing-page",
    ),
    path(
        "people/<int:person_id>/",
        views.person_detail,
        name="person-detail",
    ),
    # MOVIE DETAIL
    path("movies/<int:movie_id>/", views.movie_detail, name="movie-detail"),
]
