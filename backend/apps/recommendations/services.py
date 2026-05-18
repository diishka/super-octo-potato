from collections import defaultdict

from django.db.models import Avg, Count, Q

from apps.movies.models import Movie, UserMovie
from apps.social.models import Follow


def friend_popular_recommendations(user, limit: int = 10) -> list[dict]:
    friend_ids = Follow.objects.filter(follower=user).values_list("following_id", flat=True)
    excluded_ids = UserMovie.objects.filter(user=user).values_list("movie_id", flat=True)

    queryset = (
        UserMovie.objects.filter(user_id__in=friend_ids, status=UserMovie.Status.WATCHED)
        .exclude(movie_id__in=excluded_ids)
        .values("movie_id", "movie__title", "movie__poster_url")
        .annotate(friend_watch_count=Count("user", distinct=True), avg_friend_rating=Avg("rating"))
        .order_by("-friend_watch_count", "-avg_friend_rating")[:limit]
    )
    return list(queryset)


def similar_user_recommendations(user, limit: int = 10) -> list[dict]:
    own_ratings = dict(
        UserMovie.objects.filter(user=user, rating__isnull=False).values_list("movie_id", "rating")
    )
    if not own_ratings:
        return []

    overlap_entries = (
        UserMovie.objects.filter(movie_id__in=own_ratings.keys(), rating__isnull=False)
        .exclude(user=user)
        .select_related("user")
    )

    similarity_map = defaultdict(list)
    for entry in overlap_entries:
        similarity_map[entry.user_id].append(abs(entry.rating - own_ratings[entry.movie_id]))

    user_scores = {}
    for candidate_user_id, diffs in similarity_map.items():
        overlap = len(diffs)
        avg_diff = sum(diffs) / overlap
        user_scores[candidate_user_id] = overlap / (1 + avg_diff)

    if not user_scores:
        return []

    seen_movies = set(UserMovie.objects.filter(user=user).values_list("movie_id", flat=True))
    candidate_movies = defaultdict(lambda: {"weight": 0.0, "supporters": set(), "movie": None})

    queryset = (
        UserMovie.objects.filter(user_id__in=user_scores.keys(), rating__gte=8)
        .exclude(movie_id__in=seen_movies)
        .select_related("user", "movie")
    )

    for entry in queryset:
        bucket = candidate_movies[entry.movie_id]
        bucket["weight"] += user_scores.get(entry.user_id, 0)
        bucket["supporters"].add(entry.user.username)
        bucket["movie"] = entry.movie

    ranked = sorted(candidate_movies.values(), key=lambda item: item["weight"], reverse=True)[:limit]
    return [
        {
            "movie_id": item["movie"].id,
            "title": item["movie"].title,
            "poster_url": item["movie"].poster_url,
            "score": round(item["weight"], 2),
            "supporters": sorted(item["supporters"]),
        }
        for item in ranked
        if item["movie"] is not None
    ]


def similar_movies_recommendations(user, limit: int = 10) -> list[dict]:
    top_rated_movie_ids = list(
        UserMovie.objects.filter(user=user, rating__gte=8).values_list("movie_id", flat=True)
    )
    if not top_rated_movie_ids:
        top_rated_movie_ids = list(
            UserMovie.objects.filter(user=user, status=UserMovie.Status.WATCHED).values_list("movie_id", flat=True)[:5]
        )

    if not top_rated_movie_ids:
        return []

    seen_movies = UserMovie.objects.filter(user=user).values_list("movie_id", flat=True)
    genre_ids = Movie.objects.filter(id__in=top_rated_movie_ids).values_list("genres__id", flat=True)

    queryset = (
        Movie.objects.filter(genres__id__in=genre_ids)
        .exclude(id__in=seen_movies)
        .annotate(shared_genres=Count("genres", filter=Q(genres__id__in=genre_ids), distinct=True))
        .order_by("-shared_genres", "-tmdb_vote_average")
        .distinct()[:limit]
    )
    return [
        {
            "movie_id": movie.id,
            "title": movie.title,
            "poster_url": movie.poster_url,
            "shared_genres": movie.shared_genres,
        }
        for movie in queryset
    ]
