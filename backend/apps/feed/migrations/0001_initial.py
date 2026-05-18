from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("movies", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Activity",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("activity_type", models.CharField(choices=[("watched", "Watched"), ("rated", "Rated"), ("recommended", "Recommended")], max_length=32)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("movie", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="activities", to="movies.movie")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="activities", to=settings.AUTH_USER_MODEL)),
                ("user_movie", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="activities", to="movies.usermovie")),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="ActivityComment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("text", models.TextField(max_length=500)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("activity", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="comments", to="feed.activity")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="activity_comments", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["created_at"]},
        ),
        migrations.CreateModel(
            name="ActivityLike",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("activity", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="likes", to="feed.activity")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="activity_likes", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddConstraint(
            model_name="activitylike",
            constraint=models.UniqueConstraint(fields=("user", "activity"), name="unique_activity_like"),
        ),
    ]
