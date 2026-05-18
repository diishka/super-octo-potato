from rest_framework import serializers

from apps.accounts.models import User

from .models import Follow


class PublicUserSerializer(serializers.ModelSerializer):
    follower_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()
    is_following = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "bio",
            "avatar_url",
            "watched_count",
            "wishlist_count",
            "follower_count",
            "following_count",
            "is_following",
        )

    def get_follower_count(self, obj: User) -> int:
        return obj.incoming_follows.count()

    def get_following_count(self, obj: User) -> int:
        return obj.outgoing_follows.count()

    def get_is_following(self, obj: User) -> bool:
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return obj.incoming_follows.filter(follower=request.user).exists()


class FollowSerializer(serializers.ModelSerializer):
    follower = serializers.CharField(source="follower.username", read_only=True)
    following = PublicUserSerializer(read_only=True)

    class Meta:
        model = Follow
        fields = ("id", "follower", "following", "created_at")
