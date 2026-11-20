
from datetime import date

from django.core.management.base import BaseCommand, CommandError

from tvshows.models import TVShow
from services.tmdb import (
    get_popular_tv_shows,
    get_trending_tv_shows,
    get_top_rated_tv_shows,
    get_airing_today_tv_shows,
    get_on_the_air_tv_shows,
)


def parse_date(value):
    """Convert a TMDB date string into a Python date."""
    if not value:
        return None

    try:
        return date.fromisoformat(value)
    except (ValueError, TypeError):
        return None


class Command(BaseCommand):

    help = "Import only new TV shows from TMDB into Calypso."

    def add_arguments(self, parser):
        parser.add_argument(
            "--pages",
            type=int,
            default=5,
            help="Pages to fetch per category. Default: 5.",
        )

    def handle(self, *args, **options):

        pages = options["pages"]

        if pages < 1:
            raise CommandError("--pages must be at least 1.")

        categories = {
            "Popular": lambda page: get_popular_tv_shows(page=page),

            "Trending": lambda page: get_trending_tv_shows(
                time_window="week",
                page=page,
            ),

            "Top Rated": lambda page: get_top_rated_tv_shows(page=page),

            "Airing Today": lambda page: get_airing_today_tv_shows(
                page=page
            ),

            "On The Air": lambda page: get_on_the_air_tv_shows(
                page=page
            ),
        }

        created_count = 0
        existing_count = 0
        invalid_count = 0
        adult_count = 0

        seen_ids = set()

        self.stdout.write(
            self.style.WARNING("Starting new TV show import...")
        )

        for category, fetch_page in categories.items():

            self.stdout.write(f"\nFetching {category} TV shows...")

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

                        # Skip records already present in the database.
                        if TVShow.objects.filter(
                            tmdb_id=tmdb_id
                        ).exists():
                            existing_count += 1
                            continue

                        # Do not import records marked as adult.
                        if item.get("adult", False):
                            adult_count += 1
                            continue

                        name = (
                            item.get("name")
                            or item.get("original_name")
                            or ""
                        ).strip()

                        if not name:
                            invalid_count += 1
                            continue

                        show, created = TVShow.objects.get_or_create(
                            tmdb_id=tmdb_id,
                            defaults={
                                "name": name[:255],
                                "overview": item.get("overview") or "",
                                "poster_path": item.get("poster_path"),
                                "backdrop_path": item.get("backdrop_path"),

                                "first_air_date": parse_date(
                                    item.get("first_air_date")
                                ),

                                "last_air_date": parse_date(
                                    item.get("last_air_date")
                                ),

                                "vote_average": float(
                                    item.get("vote_average") or 0
                                ),

                                "vote_count": int(
                                    item.get("vote_count") or 0
                                ),

                                "popularity": float(
                                    item.get("popularity") or 0
                                ),

                                "original_language": (
                                    item.get("original_language") or ""
                                )[:10],

                                "original_name": (
                                    item.get("original_name") or ""
                                )[:255],

                                "origin_country": repr(
                                    item.get("origin_country") or []
                                ),

                                "is_adult": False,
                            },
                        )

                        if created:
                            created_count += 1

                            self.stdout.write(
                                self.style.SUCCESS(
                                    f"Added: {show.name} ({tmdb_id})"
                                )
                            )
                        else:
                            existing_count += 1

                    except (KeyError, ValueError, TypeError) as error:

                        invalid_count += 1

                        self.stdout.write(
                            self.style.WARNING(
                                f"Skipped invalid TV show: {error}"
                            )
                        )

        self.stdout.write("\n" + "=" * 45)
        self.stdout.write(
            self.style.SUCCESS("NEW TV SHOW IMPORT COMPLETE")
        )
        self.stdout.write("=" * 45)

        self.stdout.write(f"New TV shows added: {created_count}")
        self.stdout.write(f"Existing TV shows skipped: {existing_count}")
        self.stdout.write(f"Adult TV shows skipped: {adult_count}")
        self.stdout.write(f"Invalid records skipped: {invalid_count}")
        self.stdout.write(f"Unique TMDB IDs processed: {len(seen_ids)}")

        self.stdout.write("=" * 45)
