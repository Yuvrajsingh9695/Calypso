from django.contrib import admin

from .models import (
    Collection,
    CollectionItem,
    Watchlist,
    WatchlistItem,
)


@admin.register(Watchlist)
class WatchlistAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "created_at",
        "updated_at",
    )


@admin.register(WatchlistItem)
class WatchlistItemAdmin(admin.ModelAdmin):

    list_display = (
        "watchlist",
        "movie",
        "tv_show",
        "added_at",
    )

    list_filter = (
        "added_at",
    )


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "user",
        "is_public",
        "created_at",
        "updated_at",
    )

    list_filter = (
        "is_public",
        "created_at",
    )

    search_fields = (
        "name",
        "description",
        "user__username",
    )


@admin.register(CollectionItem)
class CollectionItemAdmin(admin.ModelAdmin):

    list_display = (
        "collection",
        "movie",
        "tv_show",
        "added_at",
    )

    list_filter = (
        "added_at",
    )