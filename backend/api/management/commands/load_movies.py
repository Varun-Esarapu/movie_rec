import csv
import os
from django.core.management.base import BaseCommand
from api.models import Movie

class Command(BaseCommand):
    help = "Ingest MovieLens 32M movies.csv and links.csv into the Movie database table"

    def handle(self, *args, **options):
        movies_path = os.path.join("data", "raw", "movies.csv")
        links_path = os.path.join("data", "raw", "links.csv")

        if not os.path.exists(movies_path) or not os.path.exists(links_path):
            self.stderr.write(self.style.ERROR("Data files not found in ./data/raw/"))
            return

        self.stdout.write("Reading links.csv for TMDB IDs...")
        tmdb_map = {}
        with open(links_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                movie_id = int(row["movieId"])
                tmdb_id = row.get("tmdbId")
                if tmdb_id and tmdb_id.strip():
                    try:
                        tmdb_map[movie_id] = int(tmdb_id.strip())
                    except ValueError:
                        pass

        self.stdout.write("Loading movies.csv into Movie table...")
        movies_to_create = []
        batch_size = 5000
        count = 0

        with open(movies_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                m_id = int(row["movieId"])
                title = row["title"]
                genres = row.get("genres", "")
                tmdb_id = tmdb_map.get(m_id)

                movies_to_create.append(
                    Movie(
                        movie_id=m_id,
                        title=title,
                        genres=genres,
                        tmdb_id=tmdb_id
                    )
                )

                if len(movies_to_create) >= batch_size:
                    Movie.objects.bulk_create(movies_to_create, ignore_conflicts=True)
                    count += len(movies_to_create)
                    self.stdout.write(f"Loaded {count:,} movies...")
                    movies_to_create = []

            if movies_to_create:
                Movie.objects.bulk_create(movies_to_create, ignore_conflicts=True)
                count += len(movies_to_create)

        self.stdout.write(self.style.SUCCESS(f"Finished loading {count:,} movies into database."))
