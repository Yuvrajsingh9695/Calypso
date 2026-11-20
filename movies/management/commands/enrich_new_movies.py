
from datetime import datetime, timezone as dt_timezone

from django.core.management.base import BaseCommand, CommandError

from movies.models import Movie
from services.tmdb import get_movie_details, get_movie_credits


START = datetime(2026, 11, 19, 11, 32, 0, tzinfo=dt_timezone.utc)
END = datetime(2026, 11, 19, 11, 33, 0, tzinfo=dt_timezone.utc)


class Command(BaseCommand):
    help = "Enrich only the movies imported on November 19, 2026."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show matching records without making API calls or changes.",
        )

    def handle(self, *args, **options):
        movies = Movie.objects.filter(
            created_at__gte=START,
            created_at__lt=END,
        ).order_by("created_at")

        total = movies.count()

        self.stdout.write(f"Target movies: {total}")

        if options["dry_run"]:
            for movie in movies:
                self.stdout.write(
                    f"{movie.tmdb_id} - {movie.title}"
                )
            self.stdout.write(
                self.style.SUCCESS("Dry run complete. No changes made.")
            )
            return

        if total != 86:
            raise CommandError(
                f"Expected 86 imported movies, found {total}. "
                "Stopped to protect existing records."
            )

        enriched = 0
        failed = 0

        for movie in movies.iterator():
            self.stdout.write(
                f"\nFetching: {movie.title} ({movie.tmdb_id})"
            )

            details = get_movie_details(movie.tmdb_id)

            if not details:
                failed += 1
                self.stdout.write(
                    self.style.WARNING("Details request failed. Skipped.")
                )
                continue

            credits = get_movie_credits(movie.tmdb_id) or {}

            cast = credits.get("cast", [])
            crew = credits.get("crew", [])

            directors = [
                person.get("name")
                for person in crew
                if person.get("job") == "Director"
                and person.get("name")
            ]

            writers = [
                person.get("name")
                for person in crew
                if person.get("job") in (
                    "Writer", "Screenplay", "Story"
                )
                and person.get("name")
            ]

            movie.runtime = details.get("runtime") or 0

            movie.genres = repr(details.get("genres") or [])

            movie.cast = repr([
                {
                    "id": person.get("id"),
                    "name": person.get("name"),
                    "character": person.get("character"),
                    "profile_path": person.get("profile_path"),
                }
                for person in cast[:20]
            ])

            movie.director = ", ".join(dict.fromkeys(directors))
            movie.writers = repr(list(dict.fromkeys(writers)))

            if details.get("backdrop_path"):
                movie.backdrop_path = details["backdrop_path"]

            movie.save(update_fields=[
                "runtime",
                "genres",
                "cast",
                "director",
                "writers",
                "backdrop_path",
            ])

            enriched += 1

            self.stdout.write(
                self.style.SUCCESS(f"Enriched: {movie.title}")
            )

        self.stdout.write("\n" + "=" * 40)
        self.stdout.write("MOVIE ENRICHMENT COMPLETE")
        self.stdout.write(f"Enriched: {enriched}")
        self.stdout.write(f"Failed: {failed}")
        self.stdout.write("=" * 40)
