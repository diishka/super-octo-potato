import django.core.validators
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Genre",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=64, unique=True)),
                ("slug", models.SlugField(max_length=64, unique=True)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="Movie",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("tmdb_id", models.PositiveIntegerField(unique=True)),
                ("media_type", models.CharField(choices=[("movie", "Movie"), ("series", "Series"), ("anime", "Anime")], default="movie", max_length=20)),
                ("title", models.CharField(max_length=255)),
                ("original_title", models.CharField(blank=True, max_length=255)),
                ("description", models.TextField(blank=True)),
                ("release_year", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("poster_url", models.URLField(blank=True)),
                ("backdrop_url", models.URLField(blank=True)),
                ("tmdb_vote_average", models.DecimalField(blank=True, decimal_places=1, max_digits=3, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("genres", models.ManyToManyField(blank=True, related_name="movies", to="movies.genre")),
            ],
            options={"ordering": ["title"]},
        ),
        migrations.CreateModel(
            name="MovieLink",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("source_name", models.CharField(max_length=80)),
                ("url", models.URLField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("added_by", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="submitted_links", to=settings.AUTH_USER_MODEL)),
                ("movie", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="streaming_links", to="movies.movie")),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="UserMovie",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(choices=[("watched", "Watched"), ("plan_to_watch", "Plan to watch")], max_length=32)),
                ("rating", models.PositiveSmallIntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(10)])),
                ("review", models.TextField(blank=True)),
                ("recommended_to_followers", models.BooleanField(default=False)),
                ("watched_at", models.DateField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("movie", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="user_entries", to="movies.movie")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="movie_entries", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-updated_at"]},
        ),
        migrations.CreateModel(
            name="LinkVote",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("value", models.SmallIntegerField(choices=[(-1, "Downvote"), (1, "Upvote")], default=1)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("link", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="votes", to="movies.movielink")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="link_votes", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddConstraint(
            model_name="usermovie",
            constraint=models.UniqueConstraint(fields=("user", "movie"), name="unique_user_movie_entry"),
        ),
        migrations.AddConstraint(
            model_name="linkvote",
            constraint=models.UniqueConstraint(fields=("user", "link"), name="unique_link_vote"),
        ),
    ]
