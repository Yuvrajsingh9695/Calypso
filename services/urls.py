
from django.urls import path
from . import views

urlpatterns = [
    path("", views.global_search, name="global-search"),
    path(
        "person/<int:person_id>/",
        views.person_detail,
        name="person-detail",
    ),
]
