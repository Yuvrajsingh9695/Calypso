
from datetime import date

from django.core.management.base import BaseCommand, CommandError

from movies.models import Movie
from services.tmdb import (
    get_popular_movies,
    get_trending_movies,
    get_top_rated_movies,
    get_upcoming_movies,
    get_now_playing_movies,
)


class Command(BaseCommand):

    help = "Import only new movies from TMDB into Calypso."

    def add_arguments(self, parser):
        parser.add_argument(
            "--pages",
            type=int,
            default=5,
            help="Pages to fetch per category. Default: 5.",
        )

        parser.add_argument(
            "--region",
            type=str,
            default="IN",
            help="Release region. Default: IN.",
        )

    def handle(self, *args, **options):

        pages = options["pages"]
        region = options["region"].upper()

        if pages < 1:
            raise CommandError("--pages must be at least 1.")

        categories = {
            "Popular": lambda page: get_popular_movies(page=page),
            "Trending": lambda page: get_trending_movies(
                time_window="week", page=page
            ),
            "Top Rated": lambda page: get_top_rated_movies(page=page),
            "Upcoming": lambda page: get_upcoming_movies(
                page=page, region=region
            ),
            "Now Playing": lambda page: get_now_playing_movies(
                page=page, region=region
            ),
        }

        created_count = 0
        skipped_count = 0
        seen_ids = set()

        self.stdout.write(
            self.style.WARNING("Starting new movie import...")
        )

        for category, fetch_page in categories.items():

            self.stdout.write(f"\nFetching {category} movies...")

            for page in range(1, pages + 1):

                response = fetch_page(page)

                if response is None:
                    raise CommandError(
                        f"TMDB request failed: {category}, page {page}. "
                        "Import stopped."
                    )

                results = response.get("results", [])

                if not results:
                    break

                for item in results:

                    try:
                        tmdb_id = int(item["id"])

                        if tmdb_id in seen_ids:
                            continue

                        seen_ids.add(tmdb_id)

                        # Never modify an existing database record.
                        if Movie.objects.filter(
                            tmdb_id=tmdb_id
                        ).exists():
                            skipped_count += 1
                            continue

                        title = (
                            item.get("title")
                            or item.get("original_title")
                            or ""
                        ).strip()

                        if not title:
                            skipped_count += 1
                            continue

                        release_date_string = (
                            item.get("release_date") or ""
                        )

                        release_date = (
                            date.fromisoformat(release_date_string)
                            if release_date_string
                            else None
                        )

                        movie = Movie(
                            tmdb_id=tmdb_id,
                            title=title[:255],
                            overview=item.get("overview") or "",
                            release_date=release_date,
                            original_language=(
                                item.get("original_language") or ""
                            )[:10],
                            vote_average=float(
                                item.get("vote_average") or 0
                            ),
                            vote_count=int(
                                item.get("vote_count") or 0
                            ),
                            popularity=float(
                                item.get("popularity") or 0
                            ),
                            poster_path=item.get("poster_path"),
                            backdrop_path=item.get("backdrop_path"),
                            genres=repr(item.get("genre_ids") or []),
                        )

                        movie.save()
                        created_count += 1

                        self.stdout.write(
                            self.style.SUCCESS(
                                f"Added: {movie.title} ({tmdb_id})"
                            )
                        )

                    except (KeyError, ValueError, TypeError) as error:

                        skipped_count += 1

                        self.stdout.write(
                            self.style.WARNING(
                                f"Skipped invalid movie: {error}"
                            )
                        )

        self.stdout.write("\n" + "=" * 45)
        self.stdout.write(
            self.style.SUCCESS("NEW MOVIE IMPORT COMPLETE")
        )
        self.stdout.write("=" * 45)

        self.stdout.write(f"New movies added: {created_count}")
        self.stdout.write(f"Existing/invalid movies skipped: {skipped_count}")
        self.stdout.write(f"Unique TMDB IDs processed: {len(seen_ids)}")
        self.stdout.write("=" * 45)
