import csv

from django.core.management.base import BaseCommand

from movies.models import Movie


class Command(BaseCommand):

    help = "Import cleaned movie dataset into Django database"

    def add_arguments(self, parser):

        parser.add_argument("csv_file", type=str)

    def handle(self, *args, **options):

        csv_file = options["csv_file"]

        batch = []

        batch_size = 5000

        total = 0

        self.stdout.write(self.style.WARNING("Starting movie import..."))

        with open(
            csv_file, "r", encoding="utf-8", errors="replace", newline=""
        ) as file:

            reader = csv.DictReader(file)

            for row in reader:

                try:

                    movie = Movie(
                        tmdb_id=int(row["id"]),
                        title=row["title"][:255],
                        overview=row["overview"],
                        release_date=(
                            row["release_date"] if row["release_date"] else None
                        ),
                        runtime=int(float(row["runtime"] or 0)),
                        original_language=(row["original_language"][:10]),
                        genres=row["genres"],
                        cast=row["cast"],
                        director=row["director"][:500],
                        writers=row["writers"],
                        vote_average=float(row["vote_average"] or 0),
                        vote_count=int(float(row["vote_count"] or 0)),
                        popularity=float(row["popularity"] or 0),
                        imdb_rating=float(row["imdb_rating"] or 0),
                        imdb_votes=int(float(row["imdb_votes"] or 0)),
                        poster_path=(row["poster_path"] or None),
                        keywords=row["keywords"],
                        certification_us=(row["certification_us"][:20]),
                    )

                    batch.append(movie)

                    if len(batch) >= batch_size:

                        Movie.objects.bulk_create(
                            batch, batch_size=batch_size, ignore_conflicts=True
                        )

                        total += len(batch)

                        self.stdout.write(f"Imported approximately {total:,} movies")

                        batch.clear()

                except Exception as e:

                    self.stdout.write(
                        self.style.ERROR(f"Skipped movie {row.get('title')}: {e}")
                    )

            if batch:

                Movie.objects.bulk_create(
                    batch, batch_size=batch_size, ignore_conflicts=True
                )

                total += len(batch)

        self.stdout.write(
            self.style.SUCCESS(f"Import complete. Processed {total:,} movies.")
        )
