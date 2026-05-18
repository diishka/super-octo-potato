from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.movies.models import Movie, UserMovie
from apps.social.models import Follow

from .models import Activity, ActivityComment


class FeedApiTests(APITestCase):
    def setUp(self):
        self.viewer = User.objects.create_user(username="viewer", email="viewer@example.com", password="strongpass123")
        self.friend = User.objects.create_user(username="friend", email="friend@example.com", password="strongpass123")
        Follow.objects.create(follower=self.viewer, following=self.friend)
        self.movie = Movie.objects.create(tmdb_id=1001, title="Upgrade", media_type="movie")
        self.activity = Activity.objects.create(
            user=self.friend,
            movie=self.movie,
            activity_type=Activity.ActivityType.WATCHED,
            metadata={"rating": 8},
        )
        ActivityComment.objects.create(activity=self.activity, user=self.friend, text="Unexpectedly brutal and fun.")
        self.recommended_entry = UserMovie.objects.create(
            user=self.friend,
            movie=self.movie,
            status="watched",
            rating=9,
            recommended_to_followers=True,
        )
        self.queue_movie = Movie.objects.create(tmdb_id=1002, title="Paprika", media_type="anime")
        UserMovie.objects.create(
            user=self.friend,
            movie=self.queue_movie,
            status="plan_to_watch",
        )
        self.client.force_authenticate(user=self.viewer)

    def test_feed_includes_followed_activity_and_comments(self):
        response = self.client.get("/api/feed/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["movie"]["title"], "Upgrade")
        self.assertEqual(response.data[0]["comments"][0]["text"], "Unexpectedly brutal and fun.")

    def test_overview_returns_recommendations_and_watchlist(self):
        response = self.client.get("/api/feed/overview/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["hero_entry"]["movie"]["title"], "Upgrade")
        self.assertEqual(response.data["friend_recommendations"][0]["user"]["username"], "friend")
        self.assertEqual(response.data["friend_watchlist"][0]["movie"]["title"], "Paprika")
