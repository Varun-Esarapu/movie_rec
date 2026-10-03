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

class UserRecommendationsView(APIView):
    def get(self, request, user_id):
        limit = int(request.query_params.get('limit', 10))
        recs = Recommendation.objects.filter(user_id=user_id).select_related('movie').order_by('rank')[:limit]
        
        # Fallback to popular items if user has no precomputed recommendations (cold-start mitigation)
        if not recs.exists():
            popular_movies = Movie.objects.filter(tmdb_id__isnull=False)[:limit]
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

        serializer = RecommendationSerializer(recs, many=True)
        return Response({"user_id": user_id, "fallback": False, "results": serializer.data}, status=status.HTTP_200_OK)

class SubmitRatingView(APIView):
    def post(self, request):
        serializer = UserRatingStagingSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Rating recorded successfully", "data": serializer.data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

from api.recommender import get_similar_movies_for_target, search_movies_hybrid, fetch_movie_credits_and_details

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
            return Response({"error": "Movie not found"}, status=status.HTTP_404_NOT_FOUND)

        results = get_similar_movies_for_target(target, limit=limit)
        details = fetch_movie_credits_and_details(target.tmdb_id)
        
        source_data = MovieSerializer(target).data
        source_data["details"] = details

        return Response({
            "source_movie": source_data,
            "results": results
        })