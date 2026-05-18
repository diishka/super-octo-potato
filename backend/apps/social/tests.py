from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User

from .models import Follow


class SocialApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="runner", email="runner@example.com", password="strongpass123")
        self.target = User.objects.create_user(username="glitch", email="glitch@example.com", password="strongpass123")

    def test_follow_toggle_creates_and_removes_relation(self):
        self.client.force_authenticate(user=self.user)

        create_response = self.client.post(f"/api/social/profiles/{self.target.username}/follow/")
        remove_response = self.client.post(f"/api/social/profiles/{self.target.username}/follow/")

        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(remove_response.status_code, status.HTTP_200_OK)
        self.assertFalse(Follow.objects.filter(follower=self.user, following=self.target).exists())

    def test_user_search_returns_matching_profiles(self):
        response = self.client.get("/api/social/users/?q=gli")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["username"], "glitch")
