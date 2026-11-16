
from urllib.parse import quote_plus

from django.db import models
from django.utils import timezone


class Movie(models.Model):

    tmdb_id = models.IntegerField(
        unique=True,
        db_index=True,
    )

    title = models.CharField(
        max_length=255,
        db_index=True,
    )

    overview = models.TextField(
        blank=True,
    )

    release_date = models.DateField(
        null=True,
        blank=True,
        db_index=True,
    )

    is_now_playing = models.BooleanField(
        default=False,
        db_index=True,
    )

    runtime = models.IntegerField(
        default=0,
    )

    original_language = models.CharField(
        max_length=10,
        blank=True,
    )

    genres = models.TextField(
        blank=True,
    )

    cast = models.TextField(
        blank=True,
    )

    director = models.CharField(
        max_length=500,
        blank=True,
    )

    writers = models.TextField(
        blank=True,
    )

    vote_average = models.FloatField(
        default=0,
    )

    vote_count = models.IntegerField(
        default=0,
    )

    popularity = models.FloatField(
        default=0,
    )

    imdb_rating = models.FloatField(
        default=0,
    )

    imdb_votes = models.IntegerField(
        default=0,
    )

    poster_path = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    # TMDB backdrop image path.
    # Required by movies/views.py.
    backdrop_path = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    trailer_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
    )

    keywords = models.TextField(
        blank=True,
    )

    certification_us = models.CharField(
        max_length=20,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    # ==================================================
    # MODEL OPTIONS
    # ==================================================

    class Meta:
        ordering = ["-release_date"]

    # ==================================================
    # STRING REPRESENTATION
    # ==================================================

    def __str__(self):
        return self.title

    # ==================================================
    # RELEASE STATUS
    # ==================================================

    @property
    def release_status(self):
        """
        Dynamically determine release status using
        the release date.

        No additional database field is required.
        """

        if self.release_date is None:
            return "unknown"

        if self.release_date > timezone.localdate():
            return "upcoming"

        return "released"

    @property
    def is_upcoming(self):
        return self.release_status == "upcoming"

    @property
    def is_released(self):
        return self.release_status == "released"

    # ==================================================
    # POSTER URL
    # ==================================================

    @property
    def poster_url(self):

        if self.poster_path:
            return (
                "https://image.tmdb.org/t/p/w500"
                f"{self.poster_path}"
            )

        return None

    # ==================================================
    # BACKDROP URL
    # ==================================================

    @property
    def backdrop_url(self):

        if self.backdrop_path:
            return (
                "https://image.tmdb.org/t/p/original"
                f"{self.backdrop_path}"
            )

        return None

    # ==================================================
    # TRAILER SEARCH FALLBACK
    # ==================================================

    @property
    def trailer_search_url(self):

        query = quote_plus(
            f"{self.title} official trailer"
        )

        return (
            "https://www.youtube.com/results?search_query="
            f"{query}"
        )
