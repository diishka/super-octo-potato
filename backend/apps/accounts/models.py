from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(unique=True)
    bio = models.TextField(blank=True)
    avatar_url = models.URLField(blank=True)
    watched_count = models.PositiveIntegerField(default=0)
    wishlist_count = models.PositiveIntegerField(default=0)

    REQUIRED_FIELDS = ["email"]

    def __str__(self) -> str:
        return self.username
