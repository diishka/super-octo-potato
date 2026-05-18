from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


def healthcheck(_request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", healthcheck),
    path("api/auth/", include("apps.accounts.urls")),
    path("api/auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/movies/", include("apps.movies.urls")),
    path("api/social/", include("apps.social.urls")),
    path("api/feed/", include("apps.feed.urls")),
    path("api/recommendations/", include("apps.recommendations.urls")),
]
