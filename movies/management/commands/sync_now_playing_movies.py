
from datetime import date

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from movies.models import Movie
from services.tmdb import get_now_playing_movies


class Command(BaseCommand):

    help = (
        "Fetch all now-playing movies from TMDB and synchronize "
        "their status with Calypso."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--region",
            type=str,
            default="IN",
            help="Two-letter release region code. Default: IN.",
        )

    def handle(self, *args, **options):

        region = options["region"].upper()
        today = timezone.localdate()

        self.stdout.write(
            self.style.WARNING(
                f"Starting Now Playing synchronization for {region}..."
            )
        )

        # Fetch the first page to discover the total page count.
        first_response = get_now_playing_movies(
            page=1,
            region=region,
        )

        if not first_response or "results" not in first_response:
            raise CommandError(
                "Could not retrieve Now Playing movies from TMDB. "
                "Check your API token and internet connection."
            )

        total_pages = int(first_response.get("total_pages", 1) or 1)

        if total_pages < 1:
            raise CommandError("TMDB returned an invalid page count.")

        self.stdout.write(
            f"TMDB reports {total_pages} page(s). Fetching all pages..."
        )

        # Collect every page before changing the database.
        # If an API request fails, existing statuses remain untouched.
        all_movies = []
        seen_ids = set()
        skipped_count = 0

        for page_number in range(1, total_pages + 1):

            if page_number == 1:
                response = first_response
            else:
                response = get_now_playing_movies(
                    page=page_number,
                    region=region,
                )

            if not response or "results" not in response:
                raise CommandError(
                    f"TMDB request failed on page {page_number}. "
                    "Database synchronization was cancelled."
                )

            results = response.get("results", [])

            self.stdout.write(
                f"Fetched page {page_number}/{total_pages}: "
                f"{len(results)} movies"
            )

            for item in results:

                try:
                    tmdb_id = int(item["id"])

                    if tmdb_id in seen_ids:
                        continue

                    title = (
                        item.get("title")
                        or item.get("original_title")
                        or ""
                    ).strip()

                    release_date_string = item.get("release_date")

                    if not title or not release_date_string:
                        skipped_count += 1
                        continue

                    release_date = date.fromisoformat(
                        release_date_string
                    )

                    # A future release should not be marked Now Playing.
                    if release_date > today:
                        skipped_count += 1
                        continue

                    seen_ids.add(tmdb_id)

                    all_movies.append({
                        "tmdb_id": tmdb_id,
                        "title": title[:255],
                        "release_date": release_date,
                        "vote_average": float(
                            item.get("vote_average") or 0
                        ),
                        "vote_count": int(
                            item.get("vote_count") or 0
                        ),
                        "popularity": float(
                            item.get("popularity") or 0
                        ),
                        "poster_path": item.get("poster_path"),
                        "overview": item.get("overview"),
                        "original_language": item.get(
                            "original_language"
                        ),
                    })

                except (KeyError, ValueError, TypeError) as error:

                    skipped_count += 1

                    self.stdout.write(
                        self.style.WARNING(
                            f"Skipped invalid movie: {error}"
                        )
                    )

        # Do not accidentally remove every existing Now Playing flag
        # if TMDB returned no valid movies unexpectedly.
        if not all_movies:
            raise CommandError(
                "No valid Now Playing movies were retrieved. "
                "Existing database statuses were left unchanged."
            )

        created_count = 0
        updated_count = 0

        # Apply the synchronization only after all pages were fetched.
        with transaction.atomic():

            # Remove the previous Now Playing membership.
            Movie.objects.filter(
                is_now_playing=True
            ).update(
                is_now_playing=False
            )

            for item in all_movies:

                tmdb_id = item.pop("tmdb_id")

                defaults = {
                    "title": item["title"],
                    "release_date": item["release_date"],
                    "vote_average": item["vote_average"],
                    "vote_count": item["vote_count"],
                    "popularity": item["popularity"],
                    "is_now_playing": True,
                }

                if item["poster_path"]:
                    defaults["poster_path"] = item["poster_path"]

                if item["overview"]:
                    defaults["overview"] = item["overview"]

                if item["original_language"]:
                    defaults["original_language"] = (
                        item["original_language"][:10]
                    )

                movie, created = Movie.objects.update_or_create(
                    tmdb_id=tmdb_id,
                    defaults=defaults,
                )

                if created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Added: {movie.title}"
                        )
                    )
                else:
                    updated_count += 1
                    self.stdout.write(
                        f"Updated: {movie.title}"
                    )

        self.stdout.write("")
        self.stdout.write("=" * 45)
        self.stdout.write(
            self.style.SUCCESS(
                "NOW PLAYING SYNCHRONIZATION COMPLETE"
            )
        )
        self.stdout.write("=" * 45)

        self.stdout.write(f"Region: {region}")
        self.stdout.write(f"Movies marked Now Playing: {len(all_movies)}")
        self.stdout.write(f"New movies added: {created_count}")
        self.stdout.write(f"Existing movies updated: {updated_count}")
        self.stdout.write(f"Movies skipped: {skipped_count}")

        self.stdout.write("=" * 45)
