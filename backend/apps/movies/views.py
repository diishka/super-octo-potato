from django.db.models import Avg, Count, Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.feed.models import Activity

from .models import LinkVote, Movie, MovieLink, UserMovie
from .serializers import (
    LinkVoteSerializer,
    MovieDetailSerializer,
    MovieLinkSerializer,
    MovieLinkWriteSerializer,
    MovieSerializer,
    UserMovieSerializer,
    UserMovieUpdateSerializer,
    UserMovieWriteSerializer,
)
from .showcase import build_cached_showcase_payload, build_local_showcase_payload, refresh_catalog_showcase
from .tmdb import TMDbClient, sync_movie_from_tmdb


def refresh_user_counters(user) -> None:
    user.watched_count = UserMovie.objects.filter(user=user, status=UserMovie.Status.WATCHED).count()
    user.wishlist_count = UserMovie.objects.filter(user=user, status=UserMovie.Status.PLAN_TO_WATCH).count()
    user.save(update_fields=["watched_count", "wishlist_count"])


def create_activity_events(entry: UserMovie, payload: dict, previous_state: dict | None = None) -> None:
    previous_state = previous_state or {}
    became_watched = payload.get("status") == UserMovie.Status.WATCHED and previous_state.get("status") != UserMovie.Status.WATCHED
    rating_changed = payload.get("rating") is not None and payload.get("rating") != previous_state.get("rating")
    newly_recommended = payload.get("recommended_to_followers") and not previous_state.get("recommended_to_followers", False)

    if became_watched:
        Activity.objects.create(
            user=entry.user,
            activity_type=Activity.ActivityType.WATCHED,
            movie=entry.movie,
            user_movie=entry,
            metadata={"rating": entry.rating},
        )

    if rating_changed:
        Activity.objects.create(
            user=entry.user,
            activity_type=Activity.ActivityType.RATED,
            movie=entry.movie,
            user_movie=entry,
            metadata={"rating": entry.rating},
        )

    if newly_recommended:
        Activity.objects.create(
            user=entry.user,
            activity_type=Activity.ActivityType.RECOMMENDED,
            movie=entry.movie,
            user_movie=entry,
            metadata={"rating": entry.rating},
        )


class MovieListAPIView(generics.ListAPIView):
    serializer_class = MovieSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = (
            Movie.objects.prefetch_related("genres")
            .annotate(
                community_rating=Avg("user_entries__rating"),
                watched_by_count=Count(
                    "user_entries",
                    filter=Q(user_entries__status=UserMovie.Status.WATCHED),
                    distinct=True,
                ),
            )
            .all()
        )
        query = self.request.query_params.get("q")
        media_type = self.request.query_params.get("media_type")

        if query:
            queryset = queryset.filter(
                Q(title__icontains=query)
                | Q(original_title__icontains=query)
                | Q(description__icontains=query)
            )

        if media_type:
            queryset = queryset.filter(media_type=media_type)

        return queryset


class MovieDetailAPIView(generics.RetrieveAPIView):
    serializer_class = MovieDetailSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return (
            Movie.objects.prefetch_related("genres", "streaming_links__added_by", "streaming_links__votes", "user_entries__movie")
            .annotate(
                community_rating=Avg("user_entries__rating"),
                watched_by_count=Count(
                    "user_entries",
                    filter=Q(user_entries__status=UserMovie.Status.WATCHED),
                    distinct=True,
                ),
            )
        )


class TMDbSearchAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        query = request.query_params.get("q", "").strip()
        if not query:
            return Response({"detail": "Query parameter q is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            client = TMDbClient()
            return Response(client.search(query))
        except Exception as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class TMDbImportAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, tmdb_id: int):
        media_type = request.query_params.get("media_type", "movie")
        try:
            movie = sync_movie_from_tmdb(tmdb_id, media_type=media_type)
            return Response(MovieSerializer(movie).data, status=status.HTTP_201_CREATED)
        except Exception as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class MovieShowcaseAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, _request):
        payload = build_cached_showcase_payload()
        if payload is not None:
            return Response(payload)

        try:
            refresh_catalog_showcase(force=True)
            payload = build_cached_showcase_payload()
        except Exception:
            payload = None

        if payload is None:
            payload = build_local_showcase_payload()
        return Response(payload)


class UserMovieListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        status_filter = request.query_params.get("status")
        queryset = UserMovie.objects.filter(user=request.user).select_related("movie").prefetch_related("movie__genres")
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return Response(UserMovieSerializer(queryset, many=True).data)

    def post(self, request):
        existing_entry = None
        movie_id = request.data.get("movie_id")
        if movie_id:
            existing_entry = UserMovie.objects.filter(user=request.user, movie_id=movie_id).first()
        previous_state = (
            {
                "status": existing_entry.status,
                "rating": existing_entry.rating,
                "recommended_to_followers": existing_entry.recommended_to_followers,
            }
            if existing_entry
            else None
        )
        serializer = UserMovieWriteSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        entry = serializer.save()
        refresh_user_counters(request.user)
        create_activity_events(entry, serializer.validated_data, previous_state=previous_state)
        return Response(UserMovieSerializer(entry).data, status=status.HTTP_201_CREATED)


class PublicUserMovieListAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, username: str):
        status_filter = request.query_params.get("status")
        user = get_object_or_404(User, username=username)
        queryset = UserMovie.objects.filter(user=user).select_related("movie").prefetch_related("movie__genres")
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return Response(UserMovieSerializer(queryset, many=True).data)


class UserMovieDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, user, movie_id: int) -> UserMovie:
        return get_object_or_404(
            UserMovie.objects.select_related("movie").prefetch_related("movie__genres"),
            user=user,
            movie_id=movie_id,
        )

    def get(self, request, movie_id: int):
        entry = self.get_object(request.user, movie_id)
        return Response(UserMovieSerializer(entry).data)

    def patch(self, request, movie_id: int):
        entry = self.get_object(request.user, movie_id)
        previous_state = {
            "status": entry.status,
            "rating": entry.rating,
            "recommended_to_followers": entry.recommended_to_followers,
        }
        serializer = UserMovieUpdateSerializer(entry, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        entry = serializer.save()
        refresh_user_counters(request.user)
        create_activity_events(entry, serializer.validated_data, previous_state=previous_state)
        return Response(UserMovieSerializer(entry).data)

    def delete(self, request, movie_id: int):
        entry = self.get_object(request.user, movie_id)
        entry.delete()
        refresh_user_counters(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MovieLinkListCreateAPIView(APIView):
    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated()]
        return [AllowAny()]

    def get(self, _request, movie_id: int):
        movie = get_object_or_404(Movie, pk=movie_id)
        links = movie.streaming_links.select_related("added_by").all()
        return Response(MovieLinkSerializer(links, many=True, context={"request": _request}).data)

    def post(self, request, movie_id: int):
        movie = get_object_or_404(Movie, pk=movie_id)
        serializer = MovieLinkWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        link = serializer.save(movie=movie, added_by=request.user)
        return Response(MovieLinkSerializer(link, context={"request": request}).data, status=status.HTTP_201_CREATED)


class LinkVoteAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, link_id: int):
        link = get_object_or_404(MovieLink, pk=link_id)
        serializer = LinkVoteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        LinkVote.objects.update_or_create(
            user=request.user,
            link=link,
            defaults={"value": serializer.validated_data["value"]},
        )
        return Response(MovieLinkSerializer(link, context={"request": request}).data)
