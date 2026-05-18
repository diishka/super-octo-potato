from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.movies.models import UserMovie
from apps.social.models import Follow

from .models import Activity, ActivityComment, ActivityLike
from .serializers import (
    ActivityCommentSerializer,
    ActivityCommentWriteSerializer,
    ActivitySerializer,
    FriendLibraryEntrySerializer,
)


def get_followed_ids(user) -> list[int]:
    return list(Follow.objects.filter(follower=user).values_list("following_id", flat=True))


class FeedListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            limit = min(int(request.query_params.get("limit", 50)), 50)
        except ValueError:
            limit = 50

        followed_ids = get_followed_ids(request.user)
        followed_ids.append(request.user.id)

        queryset = (
            Activity.objects.filter(user_id__in=followed_ids)
            .select_related("user", "movie")
            .prefetch_related("likes", "comments__user", "movie__genres")
            [:limit]
        )
        serializer = ActivitySerializer(queryset, many=True, context={"request": request})
        return Response(serializer.data)


class FeedOverviewAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        followed_ids = get_followed_ids(request.user)
        if not followed_ids:
            return Response(
                {
                    "hero_entry": None,
                    "friend_recommendations": [],
                    "friend_recent_watched": [],
                    "friend_watchlist": [],
                    "feed": [],
                }
            )

        feed_items = (
            Activity.objects.filter(user_id__in=followed_ids)
            .select_related("user", "movie")
            .prefetch_related("likes", "comments__user", "movie__genres")
            [:8]
        )

        recommended_entries = (
            UserMovie.objects.filter(user_id__in=followed_ids, status=UserMovie.Status.WATCHED)
            .filter(recommended_to_followers=True)
            .select_related("user", "movie")
            .prefetch_related("movie__genres")
            .order_by("-updated_at")[:8]
        )

        if not recommended_entries:
            recommended_entries = (
                UserMovie.objects.filter(user_id__in=followed_ids, status=UserMovie.Status.WATCHED, rating__gte=8)
                .select_related("user", "movie")
                .prefetch_related("movie__genres")
                .order_by("-rating", "-updated_at")[:8]
            )

        recent_watched = (
            UserMovie.objects.filter(user_id__in=followed_ids, status=UserMovie.Status.WATCHED)
            .select_related("user", "movie")
            .prefetch_related("movie__genres")
            .order_by("-updated_at")[:8]
        )

        watchlist_entries = (
            UserMovie.objects.filter(user_id__in=followed_ids, status=UserMovie.Status.PLAN_TO_WATCH)
            .select_related("user", "movie")
            .prefetch_related("movie__genres")
            .order_by("-updated_at")[:8]
        )

        hero_entry = recommended_entries[0] if recommended_entries else (recent_watched[0] if recent_watched else None)

        return Response(
            {
                "hero_entry": FriendLibraryEntrySerializer(hero_entry, context={"request": request}).data
                if hero_entry
                else None,
                "friend_recommendations": FriendLibraryEntrySerializer(
                    recommended_entries,
                    many=True,
                    context={"request": request},
                ).data,
                "friend_recent_watched": FriendLibraryEntrySerializer(
                    recent_watched,
                    many=True,
                    context={"request": request},
                ).data,
                "friend_watchlist": FriendLibraryEntrySerializer(
                    watchlist_entries,
                    many=True,
                    context={"request": request},
                ).data,
                "feed": ActivitySerializer(feed_items, many=True, context={"request": request}).data,
            }
        )


class ActivityLikeToggleAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, activity_id: int):
        activity = get_object_or_404(Activity, pk=activity_id)
        like, created = ActivityLike.objects.get_or_create(user=request.user, activity=activity)
        if not created:
            like.delete()
            return Response(ActivitySerializer(activity, context={"request": request}).data, status=status.HTTP_200_OK)
        return Response(ActivitySerializer(activity, context={"request": request}).data, status=status.HTTP_201_CREATED)


class ActivityCommentCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, activity_id: int):
        activity = get_object_or_404(Activity, pk=activity_id)
        serializer = ActivityCommentWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comment = ActivityComment.objects.create(
            activity=activity,
            user=request.user,
            text=serializer.validated_data["text"],
        )
        return Response(ActivityCommentSerializer(comment).data, status=status.HTTP_201_CREATED)
