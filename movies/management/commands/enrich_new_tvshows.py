from datetime import datetime, timezone as dt_timezone

from django.core.management.base import BaseCommand, CommandError

from tvshows.models import TVShow
from services.tmdb import get_tv_details, get_tv_credits

START = datetime(2026, 11, 19, 11, 35, 0, tzinfo=dt_timezone.utc)
END = datetime(2026, 11, 19, 11, 38, 0, tzinfo=dt_timezone.utc)


class Command(BaseCommand):
    help = "Enrich only the TV shows imported on November 19, 2026."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show matching records without making API calls or changes.",
        )

    def handle(self, *args, **options):
        shows = TVShow.objects.filter(
            created_at__gte=START,
            created_at__lt=END,
        ).order_by("created_at")

        total = shows.count()

        self.stdout.write(f"Target TV shows: {total}")

        if options["dry_run"]:
            for show in shows:
                self.stdout.write(f"{show.tmdb_id} - {show.name}")
            self.stdout.write(self.style.SUCCESS("Dry run complete. No changes made."))
            return

        if total != 111:
            raise CommandError(
                f"Expected 111 imported TV shows, found {total}. "
                "Stopped to protect existing records."
            )

        enriched = 0
        failed = 0

        for show in shows.iterator():
            self.stdout.write(f"\nFetching: {show.name} ({show.tmdb_id})")

            details = get_tv_details(show.tmdb_id)

            if not details:
                failed += 1
                self.stdout.write(
                    self.style.WARNING("Details request failed. Skipped.")
                )
                continue

            credits = get_tv_credits(show.tmdb_id) or {}

            show.name = (details.get("name") or show.name)[:255]

            show.overview = details.get("overview") or show.overview
            show.poster_path = details.get("poster_path") or show.poster_path
            show.backdrop_path = details.get("backdrop_path") or show.backdrop_path

            show.first_air_date = details.get("first_air_date") or show.first_air_date
            show.last_air_date = details.get("last_air_date") or show.last_air_date

            show.vote_average = details.get("vote_average") or show.vote_average
            show.vote_count = details.get("vote_count") or show.vote_count
            show.popularity = details.get("popularity") or show.popularity

            show.original_language = (details.get("original_language") or "")[:10]

            show.original_name = (details.get("original_name") or "")[:255]

            show.number_of_seasons = details.get("number_of_seasons") or 0
            show.number_of_episodes = details.get("number_of_episodes") or 0

            show.status = details.get("status") or ""
            show.in_production = bool(details.get("in_production"))

            show.genres = repr(details.get("genres") or [])
            show.created_by = repr(details.get("created_by") or [])
            show.origin_country = repr(details.get("origin_country") or [])
            show.production_companies = repr(details.get("production_companies") or [])

            show.tagline = details.get("tagline") or ""
            show.is_adult = bool(details.get("adult", False))

            show.save(
                update_fields=[
                    "name",
                    "overview",
                    "poster_path",
                    "backdrop_path",
                    "first_air_date",
                    "last_air_date",
                    "vote_average",
                    "vote_count",
                    "popularity",
                    "original_language",
                    "original_name",
                    "number_of_seasons",
                    "number_of_episodes",
                    "status",
                    "in_production",
                    "genres",
                    "created_by",
                    "origin_country",
                    "production_companies",
                    "tagline",
                    "is_adult",
                ]
            )

            enriched += 1

            self.stdout.write(self.style.SUCCESS(f"Enriched: {show.name}"))

        self.stdout.write("\n" + "=" * 40)
        self.stdout.write("TV SHOW ENRICHMENT COMPLETE")
        self.stdout.write(f"Enriched: {enriched}")
        self.stdout.write(f"Failed: {failed}")
        self.stdout.write("=" * 40)
