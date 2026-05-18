from django.core.management.base import BaseCommand

from apps.accounts.models import User
from apps.feed.models import Activity
from apps.movies.models import Genre, Movie, UserMovie
from apps.social.models import Follow


class Command(BaseCommand):
    help = "Seed local demo data for the Social Movie Recommender MVP."

    def handle(self, *args, **options):
        neon, _ = User.objects.get_or_create(
            username="neonfox",
            defaults={"email": "neonfox@example.com", "bio": "Cyber-noir cinephile"},
        )
        neon.set_password("password123")
        neon.save()

        ghost, _ = User.objects.get_or_create(
            username="ghostbyte",
            defaults={"email": "ghostbyte@example.com", "bio": "Anime and synthwave addict"},
        )
        ghost.set_password("password123")
        ghost.save()

        pulse, _ = User.objects.get_or_create(
            username="pulsegrid",
            defaults={"email": "pulsegrid@example.com", "bio": "High-concept sci-fi hunter"},
        )
        pulse.set_password("password123")
        pulse.save()

        Follow.objects.get_or_create(follower=neon, following=ghost)
        Follow.objects.get_or_create(follower=neon, following=pulse)

        sci_fi, _ = Genre.objects.get_or_create(slug="sci-fi", defaults={"name": "Sci-Fi"})
        anime, _ = Genre.objects.get_or_create(slug="anime", defaults={"name": "Anime"})
        thriller, _ = Genre.objects.get_or_create(slug="thriller", defaults={"name": "Thriller"})

        movies = [
            {
                "tmdb_id": 1,
                "title": "Blade Runner 2049",
                "media_type": "movie",
                "description": "A neon-soaked mystery about memory and identity.",
                "release_year": 2017,
                "poster_url": "https://image.tmdb.org/t/p/w500/gajva2L0rPYkEWjzgFlBXCAVBE5.jpg",
                "genres": [sci_fi, thriller],
            },
            {
                "tmdb_id": 2,
                "title": "Ghost in the Shell",
                "media_type": "anime",
                "description": "A philosophical cyberpunk investigation.",
                "release_year": 1995,
                "poster_url": "https://image.tmdb.org/t/p/w500/9gC88zYubjhPZ8prIvf0Lkg5aND.jpg",
                "genres": [sci_fi, anime],
            },
            {
                "tmdb_id": 3,
                "title": "Dune: Part Two",
                "media_type": "movie",
                "description": "Epic-scale sci-fi warfare and prophecy.",
                "release_year": 2024,
                "poster_url": "https://image.tmdb.org/t/p/w500/8b8R8l88Qje9dn9OE8PY05Nxl1X.jpg",
                "genres": [sci_fi],
            },
        ]

        created_movies = {}
        for item in movies:
            movie, _ = Movie.objects.update_or_create(
                tmdb_id=item["tmdb_id"],
                defaults={
                    "title": item["title"],
                    "media_type": item["media_type"],
                    "description": item["description"],
                    "release_year": item["release_year"],
                    "poster_url": item["poster_url"],
                },
            )
            movie.genres.set(item["genres"])
            created_movies[item["title"]] = movie

        watched_entries = [
            (ghost, created_movies["Ghost in the Shell"], "watched", 10, True),
            (ghost, created_movies["Blade Runner 2049"], "watched", 9, False),
            (pulse, created_movies["Dune: Part Two"], "watched", 9, True),
            (pulse, created_movies["Blade Runner 2049"], "watched", 10, False),
            (neon, created_movies["Ghost in the Shell"], "plan_to_watch", None, False),
        ]

        for user, movie, status, rating, recommended in watched_entries:
            entry, _ = UserMovie.objects.update_or_create(
                user=user,
                movie=movie,
                defaults={
                    "status": status,
                    "rating": rating,
                    "recommended_to_followers": recommended,
                },
            )
            if status == "watched":
                Activity.objects.get_or_create(
                    user=user,
                    movie=movie,
                    user_movie=entry,
                    activity_type=Activity.ActivityType.WATCHED,
                    defaults={"metadata": {"rating": rating}},
                )
            if rating is not None:
                Activity.objects.get_or_create(
                    user=user,
                    movie=movie,
                    user_movie=entry,
                    activity_type=Activity.ActivityType.RATED,
                    defaults={"metadata": {"rating": rating}},
                )
            if recommended:
                Activity.objects.get_or_create(
                    user=user,
                    movie=movie,
                    user_movie=entry,
                    activity_type=Activity.ActivityType.RECOMMENDED,
                    defaults={"metadata": {"rating": rating}},
                )

        neon.watched_count = UserMovie.objects.filter(user=neon, status=UserMovie.Status.WATCHED).count()
        neon.wishlist_count = UserMovie.objects.filter(user=neon, status=UserMovie.Status.PLAN_TO_WATCH).count()
        neon.save(update_fields=["watched_count", "wishlist_count"])

        ghost.watched_count = UserMovie.objects.filter(user=ghost, status=UserMovie.Status.WATCHED).count()
        ghost.wishlist_count = UserMovie.objects.filter(user=ghost, status=UserMovie.Status.PLAN_TO_WATCH).count()
        ghost.save(update_fields=["watched_count", "wishlist_count"])

        pulse.watched_count = UserMovie.objects.filter(user=pulse, status=UserMovie.Status.WATCHED).count()
        pulse.wishlist_count = UserMovie.objects.filter(user=pulse, status=UserMovie.Status.PLAN_TO_WATCH).count()
        pulse.save(update_fields=["watched_count", "wishlist_count"])

        self.stdout.write(self.style.SUCCESS("Demo data created. Users: neonfox / ghostbyte / pulsegrid"))
