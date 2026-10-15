from django.contrib import admin
from .models import TVShow

@admin.register(TVShow)
class TVShowAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "first_air_date",
        "vote_average",
        "vote_count",
        "popularity",
    )
    search_fields = ("name",)
    list_filter = ("original_language", "status")