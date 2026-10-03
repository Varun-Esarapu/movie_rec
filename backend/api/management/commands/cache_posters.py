import os
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from django.core.management.base import BaseCommand
from api.models import Movie

class Command(BaseCommand):
    help = "Query TMDB API to cache poster URLs for top movies"

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=100, help='Number of movies to enrich with TMDB poster URLs')

    def handle(self, *args, **options):
        api_key = os.getenv("TMDB_API_KEY", "3a1ff8b883fd4c71a563201decf380b1")
        base_image_url = os.getenv("TMDB_BASE_IMAGE_URL", "https://image.tmdb.org/t/p/w500")
        limit = options['limit']

        self.stdout.write(f"Querying TMDB for up to {limit} movies with valid tmdb_id...")
        movies = Movie.objects.filter(tmdb_id__isnull=False, poster_url__isnull=True)[:limit]
        
        session = requests.Session()
        retries = Retry(total=3, backoff_factor=0.3, status_forcelist=[429, 500, 502, 503, 504])
        session.mount('https://', HTTPAdapter(max_retries=retries))

        updated_count = 0
        for m in movies:
            try:
                url = f"https://api.themoviedb.org/3/movie/{m.tmdb_id}?api_key={api_key}&language=en-US"
                resp = session.get(url, timeout=5)
                if resp.status_code == 200:
                    data = resp.json()
                    poster_path = data.get("poster_path")
                    if poster_path:
                        m.poster_url = f"{base_image_url}{poster_path}"
                        m.save(update_fields=['poster_url'])
                        updated_count += 1
                        self.stdout.write(f"Cached poster for {m.title}: {m.poster_url}")
                time.sleep(0.05)
            except Exception as e:
                self.stderr.write(f"Failed to fetch metadata for movie {m.movie_id}: {e}")

        self.stdout.write(self.style.SUCCESS(f"Successfully cached poster URLs for {updated_count} movies."))
