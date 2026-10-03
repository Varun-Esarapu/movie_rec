import os
import pandas as pd
from django.core.management.base import BaseCommand
from api.models import Movie, Recommendation

class Command(BaseCommand):
    help = "Ingest processed recommendations Parquet file into Recommendation database table"

    def handle(self, *args, **options):
        parquet_path = os.path.join("data", "processed", "recommendations.parquet")

        if not os.path.exists(parquet_path):
            self.stderr.write(self.style.ERROR(f"Parquet file not found at: {parquet_path}"))
            return

        self.stdout.write("Reading recommendations from Parquet via Pandas...")
        df = pd.read_parquet(parquet_path)

        self.stdout.write("Fetching valid movie IDs from database for relational integrity...")
        valid_movie_ids = set(Movie.objects.values_list("movie_id", flat=True))

        self.stdout.write(f"Preparing {len(df):,} recommendation records...")
        
        # Sort values by userId and score descending to assign ranks cleanly
        df = df.sort_values(by=["userId", "score"], ascending=[True, False])

        recs_to_create = []
        batch_size = 5000
        count = 0
        current_user = None
        current_rank = 1

        for _, row in df.iterrows():
            u_id = int(row["userId"])
            m_id = int(row["movieId"])
            score = float(row["score"])

            # Skip movie IDs not found in catalog
            if m_id not in valid_movie_ids:
                continue

            if u_id != current_user:
                current_user = u_id
                current_rank = 1
            else:
                current_rank += 1

            recs_to_create.append(
                Recommendation(
                    user_id=u_id,
                    movie_id=m_id,
                    score=score,
                    rank=current_rank
                )
            )

            if len(recs_to_create) >= batch_size:
                Recommendation.objects.bulk_create(recs_to_create, ignore_conflicts=True)
                count += len(recs_to_create)
                self.stdout.write(f"Loaded {count:,} recommendations...")
                recs_to_create = []

        if recs_to_create:
            Recommendation.objects.bulk_create(recs_to_create, ignore_conflicts=True)
            count += len(recs_to_create)

        self.stdout.write(self.style.SUCCESS(f"Finished loading {count:,} recommendations into database."))
