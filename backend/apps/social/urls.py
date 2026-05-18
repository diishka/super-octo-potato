from django.urls import path

from .views import (
    FollowersListAPIView,
    FollowingListAPIView,
    FollowToggleAPIView,
    ProfileDetailAPIView,
    UserSearchListAPIView,
)


urlpatterns = [
    path("users/", UserSearchListAPIView.as_view(), name="user-search"),
    path("profiles/<str:username>/", ProfileDetailAPIView.as_view(), name="profile-detail"),
    path("profiles/<str:username>/follow/", FollowToggleAPIView.as_view(), name="profile-follow-toggle"),
    path("profiles/<str:username>/followers/", FollowersListAPIView.as_view(), name="profile-followers"),
    path("profiles/<str:username>/following/", FollowingListAPIView.as_view(), name="profile-following"),
]
