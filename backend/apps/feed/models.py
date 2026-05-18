from django.conf import settings
from django.db import models

from apps.movies.models import Movie, UserMovie


class Activity(models.Model):
    class ActivityType(models.TextChoices):
        WATCHED = "watched", "Watched"
        RATED = "rated", "Rated"
        RECOMMENDED = "recommended", "Recommended"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="activities")
    activity_type = models.CharField(max_length=32, choices=ActivityType.choices)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="activities", null=True, blank=True)
    user_movie = models.ForeignKey(
        UserMovie,
        on_delete=models.SET_NULL,
        related_name="activities",
        null=True,
        blank=True,
    )
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.user} {self.activity_type}"


class ActivityLike(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="activity_likes")
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name="likes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "activity"], name="unique_activity_like"),
        ]

    def __str__(self) -> str:
        return f"{self.user} likes {self.activity_id}"


class ActivityComment(models.Model):
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="activity_comments")
    text = models.TextField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"{self.user}: {self.text[:32]}"
