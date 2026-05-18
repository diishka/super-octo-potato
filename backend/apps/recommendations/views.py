from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .services import (
    friend_popular_recommendations,
    similar_movies_recommendations,
    similar_user_recommendations,
)


class RecommendationOverviewAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        payload = {
            "friends_popular": friend_popular_recommendations(user),
            "similar_users": similar_user_recommendations(user),
            "similar_movies": similar_movies_recommendations(user),
        }
        return Response(payload)
