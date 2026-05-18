from rest_framework import status
from rest_framework.test import APITestCase

from .models import User


class AccountApiTests(APITestCase):
    def test_user_can_register(self):
        response = self.client.post(
            "/api/auth/register/",
            {
                "username": "cybernova",
                "email": "cybernova@example.com",
                "password": "strongpass123",
                "password_confirm": "strongpass123",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username="cybernova")
        self.assertTrue(user.check_password("strongpass123"))

    def test_authenticated_user_can_fetch_own_profile(self):
        user = User.objects.create_user(username="echo", email="echo@example.com", password="strongpass123")
        self.client.force_authenticate(user=user)

        response = self.client.get("/api/auth/me/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "echo")
