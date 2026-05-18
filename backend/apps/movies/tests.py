from unittest.mock import patch
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.feed.models import Activity

from .models import (
    Genre,
    Movie,
    ShowcaseRefreshState,
    ShowcaseSection,
    ShowcaseSectionItem,
    UserMovie,
)
from .showcase import refresh_catalog_showcase


class MovieLibraryApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="neo",
            email="neo@example.com",
            password="strongpass123",
        )
        self.genre = Genre.objects.create(name="Sci-Fi", slug="sci-fi")
        self.movie = Movie.objects.create(
            tmdb_id=9001,
            title="Akira",
            media_type="anime",
            description="Neo-Tokyo and psychic chaos.",
            release_year=1988,
        )
        self.movie.genres.add(self.genre)
        self.client.force_authenticate(user=self.user)

    def test_adding_movie_to_watched_creates_feed_events(self):
        response = self.client.post(
            "/api/movies/library/",
            {
                "movie_id": self.movie.id,
                "status": "watched",
                "rating": 10,
                "review": "Absolute classic",
                "recommended_to_followers": True,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.user.refresh_from_db()
        self.assertEqual(self.user.watched_count, 1)
        self.assertEqual(Activity.objects.filter(user=self.user).count(), 3)

    def test_review_only_patch_does_not_duplicate_watch_event(self):
        UserMovie.objects.create(user=self.user, movie=self.movie, status="watched", rating=9)
        Activity.objects.create(
            user=self.user,
            movie=self.movie,
            activity_type=Activity.ActivityType.WATCHED,
            metadata={"rating": 9},
        )

        response = self.client.patch(
            f"/api/movies/library/{self.movie.id}/",
            {"review": "Still hits hard in 2026"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            Activity.objects.filter(user=self.user, activity_type=Activity.ActivityType.WATCHED).count(),
            1,
        )


class MovieShowcaseApiTests(APITestCase):
    def setUp(self):
        self.genre = Genre.objects.create(name="Sci-Fi", slug="sci-fi")
        self.movie = Movie.objects.create(
            tmdb_id=9001,
            title="Akira",
            media_type="anime",
            description="Neo-Tokyo and psychic chaos.",
            release_year=1988,
            poster_url="https://example.com/akira.jpg",
            backdrop_url="https://example.com/akira-bg.jpg",
            tmdb_vote_average=8.8,
        )
        self.movie.genres.add(self.genre)
        self.section = ShowcaseSection.objects.create(
            slug="weekly-top-anime",
            title="Аниме недели",
            section_type=ShowcaseSection.SectionType.WEEKLY_TOP,
            media_type=ShowcaseSection.MediaTypeFilter.ANIME,
            sort_order=10,
        )
        ShowcaseSectionItem.objects.create(
            section=self.section,
            movie=self.movie,
            rank=1,
            movement=ShowcaseSectionItem.Movement.NEW,
        )
        ShowcaseRefreshState.objects.create(
            key="catalog_showcase",
            last_refreshed_for=timezone.localdate(),
            last_status=ShowcaseRefreshState.RefreshStatus.SUCCESS,
        )

    def test_showcase_endpoint_reads_cached_database_sections(self):
        response = self.client.get("/api/movies/showcase/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["featured"]["local_id"], self.movie.id)
        self.assertEqual(response.data["weekly_top"]["anime"][0]["local_id"], self.movie.id)

    @patch("apps.movies.views.refresh_catalog_showcase", side_effect=RuntimeError("tmdb offline"))
    @patch("apps.movies.views.build_cached_showcase_payload", return_value=None)
    def test_showcase_endpoint_falls_back_to_local_movies(self, _build_cached_payload, _refresh_showcase):
        ShowcaseSectionItem.objects.all().delete()
        ShowcaseSection.objects.all().delete()
        ShowcaseRefreshState.objects.all().delete()
        response = self.client.get("/api/movies/showcase/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["featured"]["local_id"], self.movie.id)
        self.assertEqual(response.data["weekly_top"]["anime"][0]["title"], "Akira")


class MovieShowcaseRefreshTests(APITestCase):
    def setUp(self):
        self.movie_a = Movie.objects.create(
            tmdb_id=1001,
            title="Movie A",
            media_type="movie",
        )
        self.movie_b = Movie.objects.create(
            tmdb_id=1002,
            title="Movie B",
            media_type="movie",
        )
        self.movie_c = Movie.objects.create(
            tmdb_id=2001,
            title="Series A",
            media_type="series",
        )
        self.movie_d = Movie.objects.create(
            tmdb_id=3001,
            title="Anime A",
            media_type="anime",
        )

    @patch("apps.movies.showcase.sync_movie_from_tmdb")
    @patch("apps.movies.showcase.TMDbClient")
    def test_refresh_catalog_showcase_tracks_rank_changes(self, tmdb_client_class, sync_movie_from_tmdb_mock):
        tmdb_client = tmdb_client_class.return_value
        tmdb_client.curated_genre_rows.return_value = [
            {"slug": "movie-sci-fi", "title": "Фантастика", "media_type": "movie", "items": []},
            {"slug": "movie-action", "title": "Экшен", "media_type": "movie", "items": []},
            {"slug": "series-drama", "title": "Драма", "media_type": "series", "items": []},
            {"slug": "series-crime", "title": "Криминал", "media_type": "series", "items": []},
            {"slug": "anime-adventure", "title": "Аниме: приключения", "media_type": "anime", "items": []},
            {"slug": "anime-fantasy", "title": "Аниме: фэнтези", "media_type": "anime", "items": []},
        ]
        sync_movie_from_tmdb_mock.side_effect = lambda tmdb_id, media_type="movie": Movie.objects.get(tmdb_id=tmdb_id)

        tmdb_client.trending_weekly.side_effect = [
            [
                {"tmdb_id": 1001, "media_type": "movie", "title": "Movie A"},
                {"tmdb_id": 1002, "media_type": "movie", "title": "Movie B"},
            ],
            [{"tmdb_id": 2001, "media_type": "series", "title": "Series A"}],
            [{"tmdb_id": 3001, "media_type": "anime", "title": "Anime A"}],
        ]

        refresh_catalog_showcase(force=True, top_limit=2, genre_limit=1)

        tmdb_client.trending_weekly.side_effect = [
            [
                {"tmdb_id": 1002, "media_type": "movie", "title": "Movie B"},
                {"tmdb_id": 1001, "media_type": "movie", "title": "Movie A"},
            ],
            [{"tmdb_id": 2001, "media_type": "series", "title": "Series A"}],
            [{"tmdb_id": 3001, "media_type": "anime", "title": "Anime A"}],
        ]

        refresh_catalog_showcase(force=True, top_limit=2, genre_limit=1)

        movie_section = ShowcaseSection.objects.get(slug="weekly-top-movies")
        movie_items = list(movie_section.items.order_by("rank").select_related("movie"))

        self.assertEqual(movie_items[0].movie.tmdb_id, 1002)
        self.assertEqual(movie_items[0].movement, ShowcaseSectionItem.Movement.UP)
        self.assertEqual(movie_items[0].previous_rank, 2)
        self.assertEqual(movie_items[1].movie.tmdb_id, 1001)
        self.assertEqual(movie_items[1].movement, ShowcaseSectionItem.Movement.DOWN)
        self.assertEqual(movie_items[1].previous_rank, 1)
