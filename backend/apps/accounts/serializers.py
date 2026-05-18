from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    follower_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "bio",
            "avatar_url",
            "watched_count",
            "wishlist_count",
            "follower_count",
            "following_count",
        )
        read_only_fields = ("id", "watched_count", "wishlist_count")

    def get_follower_count(self, obj: User) -> int:
        return obj.incoming_follows.count()

    def get_following_count(self, obj: User) -> int:
        return obj.outgoing_follows.count()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ("id", "username", "email", "password", "password_confirm")
        read_only_fields = ("id",)

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        validated_data.pop("password_confirm")
        user = User(**validated_data)
        validate_password(password, user)
        user.set_password(password)
        user.save()
        return user
