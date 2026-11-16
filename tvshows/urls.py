
from django.urls import path

from . import views


urlpatterns = [
    path("", views.tv_home, name="tv-home"),

    path("shows/", views.tv_list, name="tv-shows"),

    path(
        "shows/page/<int:page>/",
        views.tv_list,
        name="tv-list-page",
    ),

    # TV EPISODE DETAIL
    path(
        "shows/<int:show_id>/season/<int:season_number>/episode/<int:episode_number>/",
        views.tv_episode_detail,
        name="tv-episode-detail",
    ),

    # TV SEASON DETAIL
    path(
        "shows/<int:show_id>/season/<int:season_number>/",
        views.tv_season_detail,
        name="tv-season-detail",
    ),

    # TV SHOW DETAIL
    path(
        "shows/<int:show_id>/",
        views.tv_detail,
        name="tv-detail",
    ),

    path(
        "genre/<str:genre>/",
        views.genre_shows,
        name="tv-genre",
    ),
]
