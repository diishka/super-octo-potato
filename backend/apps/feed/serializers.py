from rest_framework import serializers

from apps.movies.models import UserMovie
from apps.movies.serializers import MovieSerializer

from .models import Activity, ActivityComment


class FeedUserSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    avatar_url = serializers.CharField(allow_blank=True)


class ActivityCommentSerializer(serializers.ModelSerializer):
    user = FeedUserSerializer(read_only=True)

    class Meta:
        model = ActivityComment
        fields = ("id", "user", "text", "created_at", "updated_at")


class ActivitySerializer(serializers.ModelSerializer):
    user = FeedUserSerializer(read_only=True)
    movie = MovieSerializer(read_only=True)
    like_count = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()
    liked_by_me = serializers.SerializerMethodField()
    comments = ActivityCommentSerializer(many=True, read_only=True)

    class Meta:
        model = Activity
        fields = (
            "id",
            "user",
            "activity_type",
            "movie",
            "metadata",
            "created_at",
            "like_count",
            "comment_count",
            "liked_by_me",
            "comments",
        )

    def get_like_count(self, obj: Activity) -> int:
        return obj.likes.count()

    def get_comment_count(self, obj: Activity) -> int:
        return obj.comments.count()

    def get_liked_by_me(self, obj: Activity) -> bool:
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return obj.likes.filter(user=request.user).exists()


class ActivityCommentWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityComment
        fields = ("text",)


class FriendLibraryEntrySerializer(serializers.ModelSerializer):
    user = FeedUserSerializer(read_only=True)
    movie = MovieSerializer(read_only=True)

    class Meta:
        model = UserMovie
        fields = (
            "id",
            "user",
            "movie",
            "status",
            "rating",
            "review",
            "recommended_to_followers",
            "watched_at",
            "updated_at",
        )
