# movies/admin.py

from django.contrib import admin
from .models import Movie

admin.site.register(Movie)


class MovieAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "release_date",
        "rating",
        "popularity",
    )
    search_fields = ("title",)
    list_filter = ("original_language",)
