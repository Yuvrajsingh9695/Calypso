
from datetime import date

from django.core.management.base import BaseCommand, CommandError

from movies.models import Movie
from services.tmdb import get_upcoming_movies


class Command(BaseCommand):

    help = "Fetch upcoming movies from TMDB and synchronize them with Calypso."

    def add_arguments(self, parser):

        parser.add_argument(
            "--pages",
            type=int,
            default=5,
            help="Number of TMDB pages to fetch. Each page contains up to 20 movies.",
        )

        parser.add_argument(
            "--region",
            type=str,
            default="IN",
            help="Two-letter release region code. Default: IN.",
        )

    def handle(self, *args, **options):

        pages_requested = options["pages"]
        region = options["region"].upper()

        if pages_requested < 1:
            raise CommandError("--pages must be at least 1.")

        today = date.today()

        self.stdout.write(
            self.style.WARNING(
                f"Starting upcoming movie synchronization for region {region}..."
            )
        )

        # --------------------------------------------------
        # FETCH FIRST PAGE
        # --------------------------------------------------

        first_response = get_upcoming_movies(
            page=1,
            region=region,
        )

        if not first_response:
            raise CommandError(
                "Could not retrieve upcoming movies from TMDB. "
                "Check your API token and internet connection."
            )

        total_pages = int(first_response.get("total_pages", 1) or 1)

        pages_to_fetch = min(
            pages_requested,
            total_pages,
        )

        self.stdout.write(
            f"TMDB reports {total_pages} available pages."
        )

        self.stdout.write(
            f"Fetching {pages_to_fetch} page(s)..."
        )

        # --------------------------------------------------
        # COUNTERS
        # --------------------------------------------------

        created_count = 0
        updated_count = 0
        skipped_count = 0

        # --------------------------------------------------
        # PROCESS TMDB PAGES
        # --------------------------------------------------

        for page_number in range(1, pages_to_fetch + 1):

            if page_number == 1:

                response = first_response

            else:

                response = get_upcoming_movies(
                    page=page_number,
                    region=region,
                )

            if not response:

                raise CommandError(
                    f"TMDB request failed on page {page_number}. "
                    "Synchronization stopped."
                )

            results = response.get("results", [])

            self.stdout.write(
                f"Processing page {page_number}: {len(results)} movies"
            )

            # --------------------------------------------------
            # PROCESS EACH MOVIE
            # --------------------------------------------------

            for item in results:

                try:

                    tmdb_id = int(item["id"])

                    title = (
                        item.get("title")
                        or item.get("original_title")
                        or ""
                    ).strip()

                    release_date_string = item.get("release_date")

                    poster_path = item.get("poster_path")

                    # Basic validation

                    if not title or not release_date_string:

                        skipped_count += 1
                        continue

                    release_date = date.fromisoformat(
                        release_date_string
                    )

                    # Only import future releases

                    if release_date <= today:

                        skipped_count += 1
                        continue

                    # Skip movies without posters because the
                    # Upcoming Movies page currently requires one.

                    if not poster_path:

                        skipped_count += 1
                        continue

                    # --------------------------------------------------
                    # MOVIE DATA
                    # --------------------------------------------------

                    defaults = {
                        "title": title[:255],
                        "release_date": release_date,
                        "poster_path": poster_path,
                        "vote_average": float(
                            item.get("vote_average") or 0
                        ),
                        "vote_count": int(
                            item.get("vote_count") or 0
                        ),
                        "popularity": float(
                            item.get("popularity") or 0
                        ),
                    }

                    overview = item.get("overview")

                    if overview:
                        defaults["overview"] = overview

                    original_language = item.get("original_language")

                    if original_language:
                        defaults["original_language"] = (
                            original_language[:10]
                        )

                    # --------------------------------------------------
                    # CREATE OR UPDATE
                    # --------------------------------------------------

                    movie, created = Movie.objects.update_or_create(
                        tmdb_id=tmdb_id,
                        defaults=defaults,
                    )

                    if created:

                        created_count += 1

                        self.stdout.write(
                            self.style.SUCCESS(
                                f"Added: {movie.title} ({release_date})"
                            )
                        )

                    else:

                        updated_count += 1

                        self.stdout.write(
                            f"Updated: {movie.title}"
                        )

                except (KeyError, ValueError, TypeError) as error:

                    skipped_count += 1

                    self.stdout.write(
                        self.style.WARNING(
                            f"Skipped invalid TMDB movie: {error}"
                        )
                    )

        # --------------------------------------------------
        # FINAL REPORT
        # --------------------------------------------------

        self.stdout.write("")
        self.stdout.write("=" * 45)

        self.stdout.write(
            self.style.SUCCESS(
                "UPCOMING MOVIE SYNCHRONIZATION COMPLETE"
            )
        )

        self.stdout.write("=" * 45)

        self.stdout.write(
            f"New movies added: {created_count}"
        )

        self.stdout.write(
            f"Existing movies updated: {updated_count}"
        )

        self.stdout.write(
            f"Movies skipped: {skipped_count}"
        )

        self.stdout.write(
            f"Total processed: {created_count + updated_count + skipped_count}"
        )

        self.stdout.write("=" * 45)
