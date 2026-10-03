from django.urls import path
from api.views import UserRecommendationsView, SubmitRatingView, MovieSearchView, MovieSimilarView

urlpatterns = [
    path('recommendations/<int:user_id>/', UserRecommendationsView.as_view(), name='user-recommendations'),
    path('ratings/', SubmitRatingView.as_view(), name='submit-rating'),
    path('movies/search/', MovieSearchView.as_view(), name='movie-search'),
    path('movies/<int:movie_id>/similar/', MovieSimilarView.as_view(), name='movie-similar'),
]