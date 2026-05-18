from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User

from .serializers import PublicUserSerializer
from .models import Follow


class ProfileDetailAPIView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = PublicUserSerializer
    lookup_field = "username"
    permission_classes = [AllowAny]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context


class FollowToggleAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, username: str):
        target = get_object_or_404(User, username=username)
        if target == request.user:
            return Response({"detail": "You cannot follow yourself."}, status=status.HTTP_400_BAD_REQUEST)

        relation, created = Follow.objects.get_or_create(
            follower=request.user,
            following=target,
        )
        if created:
            return Response({"detail": "Follow created."}, status=status.HTTP_201_CREATED)

        relation.delete()
        return Response({"detail": "Follow removed."}, status=status.HTTP_200_OK)


class FollowingListAPIView(generics.ListAPIView):
    serializer_class = PublicUserSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        user = get_object_or_404(User, username=self.kwargs["username"])
        return User.objects.filter(incoming_follows__follower=user).order_by("username")

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context


class FollowersListAPIView(generics.ListAPIView):
    serializer_class = PublicUserSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        user = get_object_or_404(User, username=self.kwargs["username"])
        return User.objects.filter(outgoing_follows__following=user).order_by("username")

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context


class UserSearchListAPIView(generics.ListAPIView):
    serializer_class = PublicUserSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        query = self.request.query_params.get("q", "").strip()
        queryset = User.objects.all().order_by("username")
        if query:
            queryset = queryset.filter(username__icontains=query)
        return queryset[:20]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context
