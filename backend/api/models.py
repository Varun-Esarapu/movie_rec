from django.db import models

class Movie(models.Model):
    movie_id = models.IntegerField(primary_key=True)
    title = models.CharField(max_length=255)
    genres = models.CharField(max_length=255, blank=True, null=True)
    tmdb_id = models.IntegerField(blank=True, null=True)
    poster_url = models.URLField(max_length=500, blank=True, null=True)

    def __str__(self):
        return f"{self.title} (ID: {self.movie_id})"

class Recommendation(models.Model):
    user_id = models.IntegerField(db_index=True)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='recommendations')
    score = models.FloatField()
    rank = models.IntegerField(default=1)

    class Meta:
        indexes = [
            models.Index(fields=['user_id', 'rank']),
        ]
        ordering = ['rank']

    def __str__(self):
        return f"User {self.user_id} -> Movie {self.movie_id} (Score: {self.score:.2f})"

class UserRatingStaging(models.Model):
    user_id = models.IntegerField()
    movie_id = models.IntegerField()
    rating = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"User {self.user_id} rated {self.movie_id}: {self.rating}"
