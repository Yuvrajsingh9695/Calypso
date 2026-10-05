import csv
import re
from django.core.management.base import BaseCommand

from tvshows.models import TVShow


def is_adult_content(row):
    """
    Detect obvious adult/explicit TV animation entries.
    Normal Japanese anime is NOT blocked.
    """

    name = (row.get("name") or "").lower()
    overview = (row.get("overview") or "").lower()
    genres = (row.get("genres") or "").lower()
    companies = (row.get("production_companies") or "").lower()

    text = " ".join([name, overview, genres, companies])

    blocked_terms = [
        "hentai",
        "ecchi",
        "porn",
        "pornographic",
        "sexually explicit",
        "explicit sexual",
        "adult animation",
        "adult anime",
        "erotic animation",
        "erotic anime",
        "erotic",
        "18+",
        "18 plus",
        "xxx",
        "sexual content",
        "sexual intercourse",
        "sex slave",
        "incest",
        "nudity",
        "sexual violence",
    ]

    for term in blocked_terms:

        if term in text:
            return True

    return False


class Command(BaseCommand):

    help = "Import cleaned TV show dataset"

    def add_arguments(self, parser):

        parser.add_argument("csv_file", type=str)

    def handle(self, *args, **options):

        csv_file = options["csv_file"]

        batch = []

        batch_size = 5000

        total = 0

        self.stdout.write(self.style.WARNING("Starting TV show import..."))

        with open(
            csv_file, "r", encoding="utf-8", errors="replace", newline=""
        ) as file:

            reader = csv.DictReader(file)

            for row in reader:

                try:

                    tmdb_id = int(row["tmdb_id"])

                    name = (row["name"] or "").strip()

                    if not name:
                        continue

                    vote_count = int(float(row["vote_count"] or 0))

                    # Remove low-vote entries
                    if vote_count < 10:
                        continue

                    first_air_date = row["first_air_date"] or None

                    last_air_date = row["last_air_date"] or None

                    show = TVShow(
                        tmdb_id=tmdb_id,
                        name=name[:255],
                        overview=(row["overview"] or ""),
                        poster_path=(row["poster_path"] or None),
                        backdrop_path=(row["backdrop_path"] or None),
                        first_air_date=(first_air_date),
                        last_air_date=(last_air_date),
                        vote_average=float(row["vote_average"] or 0),
                        vote_count=vote_count,
                        popularity=float(row["popularity"] or 0),
                        original_language=(row["original_language"] or "")[:10],
                        original_name=(row["original_name"] or "")[:255],
                        number_of_seasons=int(float(row["number_of_seasons"] or 0)),
                        number_of_episodes=int(float(row["number_of_episodes"] or 0)),
                        status=(row["status"] or "")[:100],
                        in_production=(str(row["in_production"]).lower() == "true"),
                        genres=(row["genres"] or ""),
                        created_by=(row["created_by"] or ""),
                        origin_country=(row["origin_country"] or "")[:100],
                        production_companies=(row["production_companies"] or ""),
                        tagline=(row["tagline"] or ""),
                    )

                    batch.append(show)

                    if len(batch) >= batch_size:

                        TVShow.objects.bulk_create(
                            batch, batch_size=batch_size, ignore_conflicts=True
                        )

                        total += len(batch)

                        self.stdout.write(
                            f"Imported approximately " f"{total:,} TV shows"
                        )

                        batch.clear()

                except Exception as e:

                    self.stdout.write(
                        self.style.ERROR(
                            f"Skipped " f"{row.get('name', 'Unknown')}: " f"{e}"
                        )
                    )

            if batch:

                TVShow.objects.bulk_create(
                    batch, batch_size=batch_size, ignore_conflicts=True
                )

                total += len(batch)

        self.stdout.write(
            self.style.SUCCESS(f"TV import complete. " f"Processed {total:,} records.")
        )
