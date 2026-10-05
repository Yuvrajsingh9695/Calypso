from django.urls import path

from . import views

urlpatterns = [
    path("", views.tv_home, name="tv-home"),
    path("shows/", views.tv_list, name="tv-shows"),
    path("shows/page/<int:page>/", views.tv_list, name="tv-list-page"),
    path("shows/<int:show_id>/", views.tv_detail, name="tv-detail"),
    path("genre/<str:genre>/", views.genre_shows, name="tv-genre"),
]
