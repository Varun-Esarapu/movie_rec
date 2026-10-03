from rest_framework import serializers
from api.models import Movie, Recommendation, UserRatingStaging

class MovieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movie
        fields = ['movie_id', 'title', 'genres', 'tmdb_id', 'poster_url']

class RecommendationSerializer(serializers.ModelSerializer):
    movie = MovieSerializer(read_only=True)

    class Meta:
        model = Recommendation
        fields = ['rank', 'score', 'movie']

class UserRatingStagingSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserRatingStaging
        fields = ['user_id', 'movie_id', 'rating', 'created_at']
        read_only_fields = ['created_at']

    def validate_rating(self, value):
        if not (0.5 <= value <= 5.0):
            raise serializers.ValidationError("Rating must be between 0.5 and 5.0")
        return value
