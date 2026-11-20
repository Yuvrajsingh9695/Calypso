from django.contrib import admin
from .models import Movie


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):

    list_display = (
        "title",
        "tmdb_id",
        "release_date",
        "vote_average",
        "vote_count",
        "popularity",
        "original_language",
    )

    search_fields = (
        "title",
        "tmdb_id",
    )

    list_filter = (
        "original_language",
        "release_date",
    )

    ordering = ("-popularity",)

    list_per_page = 25
