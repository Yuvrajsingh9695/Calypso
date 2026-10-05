from django.conf import settings
from django.db import models


class Watchlist(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="watchlist"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"{self.user.username}'s Watchlist"


class WatchlistItem(models.Model):
    watchlist = models.ForeignKey(
        Watchlist,
        on_delete=models.CASCADE,
        related_name="items"
    )

    movie = models.ForeignKey(
        "movies.Movie",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="watchlist_items"
    )

    tv_show = models.ForeignKey(
        "tvshows.TVShow",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="watchlist_items"
    )

    added_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["-added_at"]

    def __str__(self):

        if self.movie:
            return f"{self.watchlist.user.username} - {self.movie.title}"

        if self.tv_show:
            return f"{self.watchlist.user.username} - {self.tv_show.title}"

        return f"{self.watchlist.user.username} - Empty item"


class Collection(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="collections"
    )

    name = models.CharField(
        max_length=100
    )

    description = models.TextField(
        blank=True
    )

    is_public = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} - {self.name}"


class CollectionItem(models.Model):
    collection = models.ForeignKey(
        Collection,
        on_delete=models.CASCADE,
        related_name="items"
    )

    movie = models.ForeignKey(
        "movies.Movie",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="collection_items"
    )

    tv_show = models.ForeignKey(
        "tvshows.TVShow",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="collection_items"
    )

    added_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["-added_at"]

    def __str__(self):

        if self.movie:
            return f"{self.collection.name} - {self.movie.title}"

        if self.tv_show:
            return f"{self.collection.name} - {self.tv_show.title}"

        return f"{self.collection.name} - Empty item"