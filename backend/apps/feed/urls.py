from django.urls import path

from .views import (
    ActivityCommentCreateAPIView,
    ActivityLikeToggleAPIView,
    FeedListAPIView,
    FeedOverviewAPIView,
)


urlpatterns = [
    path("", FeedListAPIView.as_view(), name="feed-list"),
    path("overview/", FeedOverviewAPIView.as_view(), name="feed-overview"),
    path("<int:activity_id>/like/", ActivityLikeToggleAPIView.as_view(), name="feed-like-toggle"),
    path("<int:activity_id>/comments/", ActivityCommentCreateAPIView.as_view(), name="feed-comment-create"),
]
