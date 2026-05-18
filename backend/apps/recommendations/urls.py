from django.urls import path

from .views import RecommendationOverviewAPIView


urlpatterns = [
    path("", RecommendationOverviewAPIView.as_view(), name="recommendation-overview"),
]
