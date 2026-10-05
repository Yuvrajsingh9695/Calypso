from django.db import models


class Movie(models.Model):

    tmdb_id = models.IntegerField(unique=True, db_index=True)

    title = models.CharField(max_length=255, db_index=True)

    overview = models.TextField(blank=True)

    release_date = models.DateField(null=True, blank=True, db_index=True)

    runtime = models.IntegerField(default=0)

    original_language = models.CharField(max_length=10, blank=True)

    genres = models.TextField(blank=True)

    cast = models.TextField(blank=True)

    director = models.CharField(max_length=500, blank=True)

    writers = models.TextField(blank=True)

    vote_average = models.FloatField(default=0)

    vote_count = models.IntegerField(default=0)

    popularity = models.FloatField(default=0)

    imdb_rating = models.FloatField(default=0)

    imdb_votes = models.IntegerField(default=0)

    poster_path = models.CharField(max_length=255, blank=True, null=True)

    trailer_url = models.URLField(max_length=500, blank=True, null=True)

    keywords = models.TextField(blank=True)

    certification_us = models.CharField(max_length=20, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-release_date"]

    def __str__(self):
        return self.title

    @property
    def poster_url(self):

        if self.poster_path:
            return "https://image.tmdb.org/t/p/w500" + self.poster_path

        return None

    @property
    def trailer_search_url(self):

        from urllib.parse import quote_plus

        query = f"{self.title} official trailer"

        return "https://www.youtube.com/results?search_query=" + quote_plus(query)
