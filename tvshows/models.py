
import ast
import json
from urllib.parse import quote_plus

from django.db import models


class TVShow(models.Model):

    tmdb_id = models.IntegerField(
        unique=True,
        db_index=True,
    )

    name = models.CharField(
        max_length=255,
        db_index=True,
    )

    overview = models.TextField(
        blank=True,
    )

    poster_path = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    backdrop_path = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    first_air_date = models.DateField(
        null=True,
        blank=True,
        db_index=True,
    )

    last_air_date = models.DateField(
        null=True,
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

    original_language = models.CharField(
        max_length=10,
        blank=True,
    )

    original_name = models.CharField(
        max_length=255,
        blank=True,
    )

    number_of_seasons = models.IntegerField(
        default=0,
    )

    number_of_episodes = models.IntegerField(
        default=0,
    )

    status = models.CharField(
        max_length=100,
        blank=True,
    )

    in_production = models.BooleanField(
        default=False,
    )

    genres = models.TextField(
        blank=True,
    )

    created_by = models.TextField(
        blank=True,
    )

    origin_country = models.CharField(
        max_length=100,
        blank=True,
    )

    production_companies = models.TextField(
        blank=True,
    )

    tagline = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    is_adult = models.BooleanField(
        default=False,
        db_index=True,
    )

    # ==================================================
    # INTERNAL PARSING HELPER
    # ==================================================

    @staticmethod
    def _parse_list(value):
        """
        Safely parse JSON or Python-style list strings.

        Supports:
        - JSON lists
        - Python-style lists
        - Empty values
        """

        if not value:
            return []

        if isinstance(value, list):
            return value

        if not isinstance(value, str):
            return []

        # Try JSON first.
        try:
            data = json.loads(value)

            if isinstance(data, list):
                return data

        except (json.JSONDecodeError, TypeError):
            pass

        # Fall back to Python literal parsing.
        try:
            data = ast.literal_eval(value)

            if isinstance(data, list):
                return data

        except (ValueError, SyntaxError, TypeError):
            pass

        return []

    # ==================================================
    # GENRES
    # ==================================================

    @property
    def genre_list(self):

        if not self.genres:
            return []

        data = self._parse_list(self.genres)

        if data:

            result = []

            for item in data:

                if isinstance(item, dict):
                    name = item.get("name")

                    if name:
                        result.append(name)

                elif isinstance(item, str):
                    result.append(item)

            return result

        # Backward compatibility with comma-separated values.
        return [
            item.strip()
            for item in self.genres.split(",")
            if item.strip()
        ]

    # ==================================================
    # CREATORS
    # ==================================================

    @property
    def creator_list(self):

        if not self.created_by:
            return []

        data = self._parse_list(self.created_by)

        if data:

            result = []

            for item in data:

                if isinstance(item, dict):
                    name = item.get("name")

                    if name:
                        result.append(name)

                elif isinstance(item, str):
                    result.append(item)

            return result

        # Backward compatibility with comma-separated values.
        return [
            item.strip()
            for item in self.created_by.split(",")
            if item.strip()
        ]

    # ==================================================
    # COUNTRIES
    # ==================================================

    @property
    def country_list(self):

        if not self.origin_country:
            return []

        data = self._parse_list(self.origin_country)

        if data:
            return [
                item
                for item in data
                if isinstance(item, str) and item.strip()
            ]

        return [
            item.strip()
            for item in self.origin_country.split(",")
            if item.strip()
        ]

    # ==================================================
    # PRODUCTION COMPANIES
    # ==================================================

    @property
    def production_company_list(self):

        if not self.production_companies:
            return []

        data = self._parse_list(self.production_companies)

        if not data:
            return []

        result = []

        for item in data:

            if isinstance(item, dict):

                name = item.get("name")

                if name:
                    result.append(name)

            elif isinstance(item, str) and item.strip():
                result.append(item)

        return result

    # ==================================================
    # TRAILER SEARCH FALLBACK
    # ==================================================

    @property
    def trailer_search_url(self):

        query = quote_plus(
            f"{self.name} official trailer"
        )

        return (
            "https://www.youtube.com/results?search_query="
            f"{query}"
        )

    # ==================================================
    # STRING REPRESENTATION
    # ==================================================

    def __str__(self):
        return self.name
