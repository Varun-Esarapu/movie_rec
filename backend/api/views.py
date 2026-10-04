from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api.models import Recommendation, Movie, UserRatingStaging
from api.serializers import (
    MovieSerializer,
    RecommendationSerializer,
    UserRatingStagingSerializer
)

from api.recommender import (
    get_similar_movies_for_target,
    search_movies_hybrid,
    fetch_movie_credits_and_details,
    fetch_tmdb_data
)
import urllib.parse

class UserRecommendationsView(APIView):
    def get(self, request, user_id):
        limit = int(request.query_params.get('limit', 10))
        recs = Recommendation.objects.filter(user_id=user_id).select_related('movie').order_by('rank')[:limit]
        
        # Fallback to popular items if user has no precomputed recommendations (cold-start mitigation)
        if not recs.exists():
            popular_movies = list(Movie.objects.filter(poster_url__isnull=False, tmdb_id__isnull=False)[:limit])
            data = [
                {
                    "rank": idx + 1,
                    "score": 4.5,
                    "movie": {
                        "movie_id": m.movie_id,
                        "title": m.title,
                        "genres": m.genres,
                        "tmdb_id": m.tmdb_id,
                        "poster_url": m.poster_url
                    }
                }
                for idx, m in enumerate(popular_movies)
            ]
            return Response({"user_id": user_id, "fallback": True, "results": data}, status=status.HTTP_200_OK)

        serialized_recs = RecommendationSerializer(recs, many=True).data
        for item in serialized_recs:
            m = item.get("movie", {})
            if not m.get("poster_url") and m.get("tmdb_id"):
                d = fetch_movie_credits_and_details(m["tmdb_id"])
                if d.get("poster_url"):
                    m["poster_url"] = d["poster_url"]
        return Response({"user_id": user_id, "fallback": False, "results": serialized_recs}, status=status.HTTP_200_OK)

class SubmitRatingView(APIView):
    def post(self, request):
        serializer = UserRatingStagingSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Rating recorded successfully", "data": serializer.data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class MovieSearchView(APIView):
    def get(self, request):
        query = request.query_params.get('q', '').strip()
        if not query or len(query) < 2:
            return Response([])
        results = search_movies_hybrid(query, limit=10)
        return Response(results)

class MovieSimilarView(APIView):
    def get(self, request, movie_id):
        limit = int(request.query_params.get('limit', 8))
        target = Movie.objects.filter(movie_id=movie_id).first() or Movie.objects.filter(tmdb_id=movie_id).first()
        if not target:
            # Dynamically fetch from TMDB so any movie ID works
            tmdb_info = fetch_tmdb_data(f"movie/{movie_id}")
            if tmdb_info and tmdb_info.get("id"):
                t_id = tmdb_info.get("id")
                title = tmdb_info.get("title") or tmdb_info.get("original_title") or f"Movie {movie_id}"
                poster_path = tmdb_info.get("poster_path")
                poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None
                genre_names = [g.get("name", "") for g in tmdb_info.get("genres", []) if g.get("name")]
                genres_str = "|".join(genre_names) or "Drama"
                
                target, _ = Movie.objects.get_or_create(
                    tmdb_id=t_id,
                    defaults={
                        "movie_id": t_id,
                        "title": title,
                        "genres": genres_str,
                        "poster_url": poster_url
                    }
                )
            else:
                return Response({"error": "Movie not found"}, status=status.HTTP_404_NOT_FOUND)

        # Auto-enrich missing poster or tmdb_id on target
        if not target.poster_url and target.tmdb_id:
            d = fetch_movie_credits_and_details(target.tmdb_id)
            if d.get("poster_url"):
                target.poster_url = d["poster_url"]
                try:
                    target.save(update_fields=["poster_url"])
                except Exception:
                    pass
        elif not target.tmdb_id:
            tmdb_search = fetch_tmdb_data(f"search/movie?query={urllib.parse.quote_plus(target.title)}")
            if tmdb_search and tmdb_search.get("results"):
                hit = tmdb_search["results"][0]
                target.tmdb_id = hit.get("id")
                p_path = hit.get("poster_path")
                if p_path:
                    target.poster_url = f"https://image.tmdb.org/t/p/w500{p_path}"
                try:
                    target.save(update_fields=["tmdb_id", "poster_url"])
                except Exception:
                    pass

        results = get_similar_movies_for_target(target, limit=limit)
        details = fetch_movie_credits_and_details(target.tmdb_id) if target.tmdb_id else {}
        
        # Persist and pass real poster_url if missing from local record
        if details.get("poster_url") and not target.poster_url:
            target.poster_url = details["poster_url"]
            try:
                target.save(update_fields=["poster_url"])
            except Exception:
                pass

        source_data = MovieSerializer(target).data
        if not source_data.get("poster_url") and details.get("poster_url"):
            source_data["poster_url"] = details["poster_url"]
        if details.get("title") and (not source_data.get("title") or source_data.get("title") in ("Selected Film", "")):
            source_data["title"] = details["title"]
        source_data["details"] = details

        return Response({
            "source_movie": source_data,
            "results": results
        })