import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.conf import settings
from django.template.defaultfilters import slugify

from .models import Genre, Movie


class TMDbClient:
    base_url = "https://api.themoviedb.org/3"
    image_base_url = "https://image.tmdb.org/t/p/w500"
    showcase_genres = (
        {
            "slug": "movie-sci-fi",
            "title": "Фантастика",
            "media_type": "movie",
            "genre_id": 878,
        },
        {
            "slug": "movie-action",
            "title": "Экшен",
            "media_type": "movie",
            "genre_id": 28,
        },
        {
            "slug": "series-drama",
            "title": "Драма",
            "media_type": "series",
            "genre_id": 18,
        },
        {
            "slug": "series-crime",
            "title": "Криминал",
            "media_type": "series",
            "genre_id": 80,
        },
        {
            "slug": "anime-adventure",
            "title": "Аниме: приключения",
            "media_type": "anime",
            "genre_id": "16,10759",
            "extra_params": {
                "with_origin_country": "JP",
                "with_original_language": "ja",
            },
        },
        {
            "slug": "anime-fantasy",
            "title": "Аниме: фэнтези",
            "media_type": "anime",
            "genre_id": "16,10765",
            "extra_params": {
                "with_origin_country": "JP",
                "with_original_language": "ja",
            },
        },
    )

    def __init__(self, api_key: str | None = None):
        self.api_key = (api_key or settings.TMDB_API_KEY).strip().strip('"').strip("'")
        if not self.api_key:
            raise RuntimeError("TMDB_API_KEY is not configured.")

    def _request(self, path: str, params: dict | None = None) -> dict:
        payload = {"language": "ru-RU"}
        headers = {"Accept": "application/json"}

        if self._uses_bearer_auth():
            headers["Authorization"] = f"Bearer {self.api_key}"
        else:
            payload["api_key"] = self.api_key

        if params:
            payload.update(params)
        url = f"{self.base_url}{path}?{urlencode(payload)}"
        request = Request(url, headers=headers)
        try:
            with urlopen(request, timeout=10) as response:
                return json.load(response)
        except HTTPError as exc:
            message = self._extract_http_error_message(exc)
            if exc.code == 401:
                raise RuntimeError(
                    "TMDb API key is invalid or missing. Update TMDB_API_KEY in backend settings."
                ) from exc
            raise RuntimeError(f"TMDb error {exc.code}: {message}") from exc
        except URLError as exc:
            raise RuntimeError("TMDb is temporarily unavailable. Please try again later.") from exc

    def search(self, query: str) -> list[dict]:
        data = self._request("/search/multi", {"query": query, "include_adult": "false"})
        results = []
        for item in data.get("results", []):
            if item.get("media_type") not in {"movie", "tv"}:
                continue
            results.append(self.normalize_list_item(item))
        return results

    def trending_weekly(self, media_type: str, limit: int = 6) -> list[dict]:
        normalized_media_type = self.normalize_media_type(media_type)

        if media_type == "anime":
            data = self._request("/trending/tv/week")
            items = [
                self.normalize_list_item(item, media_type="anime")
                for item in data.get("results", [])
                if self._looks_like_anime(item)
            ]
            return items[:limit]

        path = "/trending/tv/week" if normalized_media_type == "series" else "/trending/movie/week"
        data = self._request(path)
        return [
            self.normalize_list_item(item, media_type=normalized_media_type)
            for item in data.get("results", [])[:limit]
        ]

    def curated_genre_rows(self, limit_per_genre: int = 4) -> list[dict]:
        rows = []

        for genre in self.showcase_genres:
            media_type = genre["media_type"]
            normalized_media_type = "series" if media_type in {"series", "anime"} else "movie"
            params = {
                "with_genres": genre["genre_id"],
                "sort_by": "popularity.desc",
                "include_adult": "false",
                "page": 1,
            }
            params.update(genre.get("extra_params", {}))

            path = "/discover/tv" if normalized_media_type == "series" else "/discover/movie"
            data = self._request(path, params)
            items = [
                self.normalize_list_item(item, media_type=media_type)
                for item in data.get("results", [])[:limit_per_genre]
            ]
            rows.append(
                {
                    "slug": genre["slug"],
                    "title": genre["title"],
                    "media_type": media_type,
                    "items": items,
                }
            )

        return rows

    def normalize_media_type(self, media_type: str) -> str:
        return "series" if media_type in {"tv", "series", "anime"} else "movie"

    def get_title(self, tmdb_id: int, media_type: str = "movie") -> dict:
        if self.normalize_media_type(media_type) == "series":
            return self._request(f"/tv/{tmdb_id}")
        return self._request(f"/movie/{tmdb_id}")

    def normalize_movie(self, payload: dict, media_type: str = "movie") -> dict:
        normalized_media_type = "anime" if media_type == "anime" else self.normalize_media_type(media_type)
        return {
            "media_type": normalized_media_type,
            "title": payload.get("title") or payload.get("name") or "",
            "original_title": payload.get("original_title") or payload.get("original_name") or "",
            "description": payload.get("overview") or "",
            "release_year": self._extract_year(payload.get("release_date") or payload.get("first_air_date")),
            "poster_url": self._build_image_url(payload.get("poster_path")),
            "backdrop_url": self._build_image_url(payload.get("backdrop_path")),
            "tmdb_vote_average": payload.get("vote_average"),
            "genres": [genre["name"] for genre in payload.get("genres", [])],
        }

    def normalize_list_item(self, payload: dict, media_type: str | None = None) -> dict:
        resolved_media_type = media_type or payload.get("media_type") or "movie"
        normalized_media_type = (
            "anime"
            if resolved_media_type == "anime"
            else self.normalize_media_type(resolved_media_type)
        )

        return {
            "tmdb_id": payload["id"],
            "media_type": normalized_media_type,
            "title": payload.get("title") or payload.get("name") or "",
            "original_title": payload.get("original_title") or payload.get("original_name") or "",
            "description": payload.get("overview") or "",
            "release_year": self._extract_year(payload.get("release_date") or payload.get("first_air_date")),
            "poster_url": self._build_image_url(payload.get("poster_path")),
            "backdrop_url": self._build_image_url(payload.get("backdrop_path")),
            "tmdb_vote_average": payload.get("vote_average"),
        }

    def _build_image_url(self, path: str | None) -> str:
        if not path:
            return ""
        return f"{self.image_base_url}{path}"

    def _uses_bearer_auth(self) -> bool:
        return self.api_key.count(".") == 2

    def _extract_year(self, date_value: str | None) -> int | None:
        if not date_value:
            return None
        try:
            return int(date_value[:4])
        except ValueError:
            return None

    def _extract_http_error_message(self, exc: HTTPError) -> str:
        try:
            payload = json.loads(exc.read().decode("utf-8"))
        except Exception:
            payload = {}

        if isinstance(payload, dict):
            status_message = payload.get("status_message")
            if status_message:
                return status_message

        return exc.reason or "Unknown TMDb error"

    def _looks_like_anime(self, payload: dict) -> bool:
        genre_ids = payload.get("genre_ids") or []
        origin_country = payload.get("origin_country") or []

        return (
            16 in genre_ids
            or payload.get("original_language") == "ja"
            or "JP" in origin_country
        )


def sync_movie_from_tmdb(tmdb_id: int, media_type: str = "movie") -> Movie:
    client = TMDbClient()
    payload = client.get_title(tmdb_id, media_type=media_type)
    normalized = client.normalize_movie(payload, media_type=media_type)
    genre_names = normalized.pop("genres", [])

    movie, _ = Movie.objects.update_or_create(
        tmdb_id=tmdb_id,
        defaults=normalized,
    )

    genres = []
    for genre_name in genre_names:
        genre, _ = Genre.objects.get_or_create(
            slug=slugify(genre_name),
            defaults={"name": genre_name},
        )
        genres.append(genre)

    movie.genres.set(genres)
    return movie
