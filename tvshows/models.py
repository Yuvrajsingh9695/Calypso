from django.db import models
import json
import ast
from urllib.parse import quote_plus


class TVShow(models.Model):

    tmdb_id = models.IntegerField(unique=True, db_index=True)

    name = models.CharField(max_length=255, db_index=True)

    overview = models.TextField(blank=True)

    poster_path = models.CharField(max_length=255, blank=True, null=True)

    backdrop_path = models.CharField(max_length=255, blank=True, null=True)

    first_air_date = models.DateField(null=True, blank=True, db_index=True)

    last_air_date = models.DateField(null=True, blank=True)

    vote_average = models.FloatField(default=0)

    vote_count = models.IntegerField(default=0)

    popularity = models.FloatField(default=0)

    original_language = models.CharField(max_length=10, blank=True)

    original_name = models.CharField(max_length=255, blank=True)

    number_of_seasons = models.IntegerField(default=0)

    number_of_episodes = models.IntegerField(default=0)

    status = models.CharField(max_length=100, blank=True)

    in_production = models.BooleanField(default=False)

    genres = models.TextField(blank=True)

    created_by = models.TextField(blank=True)

    origin_country = models.CharField(max_length=100, blank=True)

    production_companies = models.TextField(blank=True)

    tagline = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    is_adult = models.BooleanField(default=False, db_index=True)
    
    @property
    def genre_list(self):
        if not self.genres:
            return []

        try:
            data = ast.literal_eval(self.genres)

            if isinstance(data, list):
                result = []

                for item in data:
                    if isinstance(item, dict):
                        name = item.get("name")
                        if name:
                            result.append(name)

                    elif isinstance(item, str):
                        result.append(item)

                return result

        except (ValueError, SyntaxError):
            pass

        return [item.strip() for item in self.genres.split(",") if item.strip()]

    @property
    def creator_list(self):
        if not self.created_by:
            return []

        try:
            data = ast.literal_eval(self.created_by)

            if isinstance(data, list):
                result = []

                for item in data:
                    if isinstance(item, dict):
                        name = item.get("name")
                        if name:
                            result.append(name)

                    elif isinstance(item, str):
                        result.append(item)

                return result

        except (ValueError, SyntaxError):
            pass

        return [item.strip() for item in self.created_by.split(",") if item.strip()]

    @property
    def country_list(self):
        if not self.origin_country:
            return []

        try:
            data = ast.literal_eval(self.origin_country)

            if isinstance(data, list):
                return data

        except (ValueError, SyntaxError):
            pass

        return [item.strip() for item in self.origin_country.split(",") if item.strip()]

    @property
    def production_company_list(self):
        if not self.production_companies:
            return []

        data = None

        # Try JSON first
        try:
            data = json.loads(self.production_companies)
        except (json.JSONDecodeError, TypeError):
            pass

        # Try Python-style list/dictionary
        if data is None:
            try:
                data = ast.literal_eval(self.production_companies)
            except (ValueError, SyntaxError, TypeError):
                return []

        if not isinstance(data, list):
            return []

        result = []

        for item in data:
            if isinstance(item, dict):
                name = item.get("name")

                if name:
                    result.append(name)

            elif isinstance(item, str):
                result.append(item)

        return result

    @property
    def trailer_search_url(self):
        query = quote_plus(f"{self.name} official trailer")
        return f"https://www.youtube.com/results?search_query={query}"
