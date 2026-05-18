from django.urls import path

from .views import (
    LinkVoteAPIView,
    MovieDetailAPIView,
    MovieLinkListCreateAPIView,
    MovieListAPIView,
    MovieShowcaseAPIView,
    TMDbImportAPIView,
    TMDbSearchAPIView,
    PublicUserMovieListAPIView,
    UserMovieDetailAPIView,
    UserMovieListCreateAPIView,
)


urlpatterns = [
    path("", MovieListAPIView.as_view(), name="movie-list"),
    path("showcase/", MovieShowcaseAPIView.as_view(), name="movie-showcase"),
    path("library/", UserMovieListCreateAPIView.as_view(), name="user-movie-library"),
    path("library/<int:movie_id>/", UserMovieDetailAPIView.as_view(), name="user-movie-detail"),
    path("users/<str:username>/library/", PublicUserMovieListAPIView.as_view(), name="public-user-movie-library"),
    path("tmdb/search/", TMDbSearchAPIView.as_view(), name="tmdb-search"),
    path("tmdb/import/<int:tmdb_id>/", TMDbImportAPIView.as_view(), name="tmdb-import"),
    path("links/<int:link_id>/vote/", LinkVoteAPIView.as_view(), name="link-vote"),
    path("<int:pk>/", MovieDetailAPIView.as_view(), name="movie-detail"),
    path("<int:movie_id>/links/", MovieLinkListCreateAPIView.as_view(), name="movie-links"),
]
