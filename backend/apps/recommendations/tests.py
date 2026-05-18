from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.movies.models import Movie, UserMovie
from apps.social.models import Follow


class RecommendationApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="solo", email="solo@example.com", password="strongpass123")
        self.friend = User.objects.create_user(username="ally", email="ally@example.com", password="strongpass123")
        Follow.objects.create(follower=self.user, following=self.friend)

        self.shared = Movie.objects.create(tmdb_id=2001, title="Arrival", media_type="movie")
        self.recommended = Movie.objects.create(tmdb_id=2002, title="Ex Machina", media_type="movie")

        UserMovie.objects.create(user=self.user, movie=self.shared, status="watched", rating=9)
        UserMovie.objects.create(user=self.friend, movie=self.shared, status="watched", rating=9)
        UserMovie.objects.create(user=self.friend, movie=self.recommended, status="watched", rating=10)

        self.client.force_authenticate(user=self.user)

    def test_recommendation_overview_returns_friend_based_titles(self):
        response = self.client.get("/api/recommendations/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["friends_popular"][0]["movie__title"], "Ex Machina")
