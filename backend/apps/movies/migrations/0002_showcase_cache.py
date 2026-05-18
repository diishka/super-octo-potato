from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("movies", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ShowcaseRefreshState",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("key", models.CharField(default="catalog_showcase", max_length=40, unique=True)),
                ("last_refreshed_for", models.DateField(blank=True, null=True)),
                ("last_started_at", models.DateTimeField(blank=True, null=True)),
                ("last_completed_at", models.DateTimeField(blank=True, null=True)),
                (
                    "last_status",
                    models.CharField(
                        choices=[("idle", "Idle"), ("running", "Running"), ("success", "Success"), ("failed", "Failed")],
                        default="idle",
                        max_length=16,
                    ),
                ),
                ("last_error", models.TextField(blank=True)),
                ("payload_summary", models.JSONField(blank=True, default=dict)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Showcase refresh state",
                "verbose_name_plural": "Showcase refresh states",
            },
        ),
        migrations.CreateModel(
            name="ShowcaseSection",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("slug", models.SlugField(max_length=80, unique=True)),
                ("title", models.CharField(max_length=120)),
                ("description", models.CharField(blank=True, max_length=255)),
                (
                    "section_type",
                    models.CharField(
                        choices=[("weekly_top", "Weekly top"), ("genre", "Genre")],
                        max_length=24,
                    ),
                ),
                (
                    "media_type",
                    models.CharField(
                        choices=[("movie", "Movie"), ("series", "Series"), ("anime", "Anime"), ("mixed", "Mixed")],
                        default="mixed",
                        max_length=20,
                    ),
                ),
                ("sort_order", models.PositiveSmallIntegerField(default=0)),
                ("is_active", models.BooleanField(default=True)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("refreshed_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["sort_order", "title"],
            },
        ),
        migrations.CreateModel(
            name="ShowcaseSectionItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("rank", models.PositiveSmallIntegerField()),
                ("previous_rank", models.PositiveSmallIntegerField(blank=True, null=True)),
                (
                    "movement",
                    models.CharField(
                        choices=[("new", "New"), ("up", "Up"), ("down", "Down"), ("same", "Same")],
                        default="new",
                        max_length=16,
                    ),
                ),
                ("delta", models.SmallIntegerField(default=0)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "movie",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="showcase_items", to="movies.movie"),
                ),
                (
                    "section",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="items", to="movies.showcasesection"),
                ),
            ],
            options={
                "ordering": ["rank"],
            },
        ),
        migrations.AddConstraint(
            model_name="showcasesectionitem",
            constraint=models.UniqueConstraint(fields=("section", "movie"), name="unique_showcase_movie_in_section"),
        ),
        migrations.AddConstraint(
            model_name="showcasesectionitem",
            constraint=models.UniqueConstraint(fields=("section", "rank"), name="unique_showcase_rank_in_section"),
        ),
    ]
