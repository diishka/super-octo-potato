from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Sum


class Genre(models.Model):
    name = models.CharField(max_length=64, unique=True)
    slug = models.SlugField(max_length=64, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Movie(models.Model):
    class MediaType(models.TextChoices):
        MOVIE = "movie", "Movie"
        SERIES = "series", "Series"
        ANIME = "anime", "Anime"

    tmdb_id = models.PositiveIntegerField(unique=True)
    media_type = models.CharField(max_length=20, choices=MediaType.choices, default=MediaType.MOVIE)
    title = models.CharField(max_length=255)
    original_title = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    release_year = models.PositiveSmallIntegerField(null=True, blank=True)
    poster_url = models.URLField(blank=True)
    backdrop_url = models.URLField(blank=True)
    tmdb_vote_average = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    genres = models.ManyToManyField(Genre, related_name="movies", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["title"]

    def __str__(self) -> str:
        return self.title


class UserMovie(models.Model):
    class Status(models.TextChoices):
        WATCHED = "watched", "Watched"
        PLAN_TO_WATCH = "plan_to_watch", "Plan to watch"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="movie_entries")
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="user_entries")
    status = models.CharField(max_length=32, choices=Status.choices)
    rating = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
    )
    review = models.TextField(blank=True)
    recommended_to_followers = models.BooleanField(default=False)
    watched_at = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        constraints = [
            models.UniqueConstraint(fields=["user", "movie"], name="unique_user_movie_entry"),
        ]

    def __str__(self) -> str:
        return f"{self.user} -> {self.movie} ({self.status})"


class MovieLink(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="streaming_links")
    added_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="submitted_links")
    source_name = models.CharField(max_length=80)
    url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def score(self) -> int:
        return self.votes.aggregate(total=Sum("value")).get("total") or 0

    def __str__(self) -> str:
        return f"{self.source_name}: {self.url}"


class LinkVote(models.Model):
    class VoteValue(models.IntegerChoices):
        DOWNVOTE = -1, "Downvote"
        UPVOTE = 1, "Upvote"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="link_votes")
    link = models.ForeignKey(MovieLink, on_delete=models.CASCADE, related_name="votes")
    value = models.SmallIntegerField(choices=VoteValue.choices, default=VoteValue.UPVOTE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "link"], name="unique_link_vote"),
        ]

    def __str__(self) -> str:
        return f"{self.user} -> {self.link_id} ({self.value})"


class ShowcaseSection(models.Model):
    class SectionType(models.TextChoices):
        WEEKLY_TOP = "weekly_top", "Weekly top"
        GENRE = "genre", "Genre"

    class MediaTypeFilter(models.TextChoices):
        MOVIE = "movie", "Movie"
        SERIES = "series", "Series"
        ANIME = "anime", "Anime"
        MIXED = "mixed", "Mixed"

    slug = models.SlugField(max_length=80, unique=True)
    title = models.CharField(max_length=120)
    description = models.CharField(max_length=255, blank=True)
    section_type = models.CharField(max_length=24, choices=SectionType.choices)
    media_type = models.CharField(
        max_length=20,
        choices=MediaTypeFilter.choices,
        default=MediaTypeFilter.MIXED,
    )
    sort_order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict, blank=True)
    refreshed_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "title"]

    def __str__(self) -> str:
        return self.title


class ShowcaseSectionItem(models.Model):
    class Movement(models.TextChoices):
        NEW = "new", "New"
        UP = "up", "Up"
        DOWN = "down", "Down"
        SAME = "same", "Same"

    section = models.ForeignKey(ShowcaseSection, on_delete=models.CASCADE, related_name="items")
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="showcase_items")
    rank = models.PositiveSmallIntegerField()
    previous_rank = models.PositiveSmallIntegerField(null=True, blank=True)
    movement = models.CharField(max_length=16, choices=Movement.choices, default=Movement.NEW)
    delta = models.SmallIntegerField(default=0)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["rank"]
        constraints = [
            models.UniqueConstraint(fields=["section", "movie"], name="unique_showcase_movie_in_section"),
            models.UniqueConstraint(fields=["section", "rank"], name="unique_showcase_rank_in_section"),
        ]

    def __str__(self) -> str:
        return f"{self.section.slug} -> {self.movie.title} ({self.rank})"


class ShowcaseRefreshState(models.Model):
    class RefreshStatus(models.TextChoices):
        IDLE = "idle", "Idle"
        RUNNING = "running", "Running"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"

    key = models.CharField(max_length=40, unique=True, default="catalog_showcase")
    last_refreshed_for = models.DateField(null=True, blank=True)
    last_started_at = models.DateTimeField(null=True, blank=True)
    last_completed_at = models.DateTimeField(null=True, blank=True)
    last_status = models.CharField(
        max_length=16,
        choices=RefreshStatus.choices,
        default=RefreshStatus.IDLE,
    )
    last_error = models.TextField(blank=True)
    payload_summary = models.JSONField(default=dict, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Showcase refresh state"
        verbose_name_plural = "Showcase refresh states"

    def __str__(self) -> str:
        return f"{self.key}: {self.last_status}"
