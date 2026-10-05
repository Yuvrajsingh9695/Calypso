from django.urls import path

from . import views

urlpatterns = [
    # HOME
    path("", views.home_page, name="home"),
    # MOVIES
    path("movies/", views.movie_list, name="movies"),
    path("movies/page/<int:page>/", views.movie_list, name="movie-list-page"),
    # MOVIE DETAIL
    path("movies/<int:movie_id>/", views.movie_detail, name="movie-detail"),
    # OLD PAGES
    path("movies/2/", views.movies2, name="movies-2"),
    path("movies/3/", views.movies3, name="movies-3"),
    # GENRES
    path("genre/action/", views.action, name="action"),
    path("genre/animation/", views.animation, name="animation"),
    path("genre/horror/", views.horror, name="horror"),
    path("genre/thriller/", views.thriller, name="thriller"),
    path("genre/comedy/", views.comedy, name="comedy"),
    path("genre/scifi/", views.scifi, name="scifi"),
    path("genre/drama/", views.drama, name="drama"),
    path("genre/romance/", views.romance, name="romance"),
]
