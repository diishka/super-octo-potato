from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from django.db import transaction
from django.db.models import Avg, Count, Q
from django.utils import timezone

from .models import Movie, ShowcaseRefreshState, ShowcaseSection, ShowcaseSectionItem, UserMovie
from .tmdb import TMDbClient, sync_movie_from_tmdb

SHOWCASE_REFRESH_KEY = "catalog_showcase"
SHOWCASE_SECTION_LIMIT = 12


@dataclass(frozen=True)
class WeeklyTopDefinition:
    slug: str
    title: str
    media_type: str
    sort_order: int


WEEKLY_TOP_DEFINITIONS = (
    WeeklyTopDefinition(
        slug="weekly-top-movies",
        title="Фильмы недели",
        media_type=Movie.MediaType.MOVIE,
        sort_order=10,
    ),
    WeeklyTopDefinition(
        slug="weekly-top-series",
        title="Сериалы недели",
        media_type=Movie.MediaType.SERIES,
        sort_order=20,
    ),
    WeeklyTopDefinition(
        slug="weekly-top-anime",
        title="Аниме недели",
        media_type=Movie.MediaType.ANIME,
        sort_order=30,
    ),
)


def get_showcase_state() -> ShowcaseRefreshState:
    state, _ = ShowcaseRefreshState.objects.get_or_create(key=SHOWCASE_REFRESH_KEY)
    return state


def showcase_is_stale(state: ShowcaseRefreshState | None = None) -> bool:
    state = state or get_showcase_state()
    return (
        state.last_refreshed_for != timezone.localdate()
        or state.last_status != ShowcaseRefreshState.RefreshStatus.SUCCESS
    )


def refresh_catalog_showcase(
    *,
    force: bool = False,
    top_limit: int = SHOWCASE_SECTION_LIMIT,
    genre_limit: int = SHOWCASE_SECTION_LIMIT,
) -> dict:
    state = get_showcase_state()
    today = timezone.localdate()

    if not force and not showcase_is_stale(state):
        return {"refreshed": False, "reason": "already_fresh", "summary": state.payload_summary}

    state.last_started_at = timezone.now()
    state.last_status = ShowcaseRefreshState.RefreshStatus.RUNNING
    state.last_error = ""
    state.save(update_fields=["last_started_at", "last_status", "last_error", "updated_at"])

    client = TMDbClient()

    try:
        weekly_rows = [
            {
                "slug": definition.slug,
                "title": definition.title,
                "description": "Ежедневно сверяется с текущим top week в TMDb.",
                "section_type": ShowcaseSection.SectionType.WEEKLY_TOP,
                "media_type": definition.media_type,
                "sort_order": definition.sort_order,
                "items": client.trending_weekly(definition.media_type, limit=top_limit),
            }
            for definition in WEEKLY_TOP_DEFINITIONS
        ]
        genre_rows = []

        for index, row in enumerate(client.curated_genre_rows(limit_per_genre=genre_limit), start=1):
            genre_rows.append(
                {
                    "slug": row["slug"],
                    "title": row["title"],
                    "description": "Кэшируется локально и отдается из базы без ожидания внешнего API.",
                    "section_type": ShowcaseSection.SectionType.GENRE,
                    "media_type": row["media_type"],
                    "sort_order": 100 + index,
                    "items": row["items"],
                }
            )

        summary = _persist_sections([*weekly_rows, *genre_rows])
        state.last_refreshed_for = today
        state.last_completed_at = timezone.now()
        state.last_status = ShowcaseRefreshState.RefreshStatus.SUCCESS
        state.last_error = ""
        state.payload_summary = summary
        state.save(
            update_fields=[
                "last_refreshed_for",
                "last_completed_at",
                "last_status",
                "last_error",
                "payload_summary",
                "updated_at",
            ]
        )
        return {"refreshed": True, "reason": "updated", "summary": summary}
    except Exception as exc:
        state.last_completed_at = timezone.now()
        state.last_status = ShowcaseRefreshState.RefreshStatus.FAILED
        state.last_error = str(exc)
        state.save(
            update_fields=[
                "last_completed_at",
                "last_status",
                "last_error",
                "updated_at",
            ]
        )
        raise


def build_cached_showcase_payload() -> dict | None:
    state = get_showcase_state()
    sections = list(
        ShowcaseSection.objects.filter(is_active=True)
        .prefetch_related("items__movie")
        .order_by("sort_order", "title")
    )

    if not sections:
        return None

    weekly_top = {
        Movie.MediaType.MOVIE: [],
        Movie.MediaType.SERIES: [],
        Movie.MediaType.ANIME: [],
    }
    genres = []

    for section in sections:
        items = [_serialize_showcase_item(item) for item in section.items.all()]
        serialized_section = {
            "slug": section.slug,
            "title": section.title,
            "description": section.description,
            "media_type": section.media_type,
            "items": items,
        }

        if section.section_type == ShowcaseSection.SectionType.WEEKLY_TOP:
            weekly_top[section.media_type] = items
        else:
            genres.append(serialized_section)

    featured = (
        weekly_top[Movie.MediaType.MOVIE][:1]
        or weekly_top[Movie.MediaType.ANIME][:1]
        or weekly_top[Movie.MediaType.SERIES][:1]
    )

    return {
        "featured": featured[0] if featured else None,
        "weekly_top": weekly_top,
        "genres": genres,
        "last_refreshed_for": state.last_refreshed_for.isoformat() if state.last_refreshed_for else None,
        "last_completed_at": state.last_completed_at.isoformat() if state.last_completed_at else None,
        "stale": showcase_is_stale(state),
    }


def build_local_showcase_payload(limit: int = SHOWCASE_SECTION_LIMIT) -> dict:
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
        .order_by("-community_rating", "-tmdb_vote_average", "-watched_by_count", "title")
    )
    weekly_top = {
        Movie.MediaType.MOVIE: _serialize_movie_queryset(queryset.filter(media_type=Movie.MediaType.MOVIE)[:limit]),
        Movie.MediaType.SERIES: _serialize_movie_queryset(queryset.filter(media_type=Movie.MediaType.SERIES)[:limit]),
        Movie.MediaType.ANIME: _serialize_movie_queryset(queryset.filter(media_type=Movie.MediaType.ANIME)[:limit]),
    }
    genres = []

    genre_candidates = (
        queryset.filter(genres__isnull=False)
        .values("genres__slug", "genres__name")
        .annotate(movie_count=Count("id", distinct=True))
        .order_by("-movie_count", "genres__name")
    )

    seen_slugs = set()
    sort_order = 100
    for row in genre_candidates:
        slug = row["genres__slug"]
        title = row["genres__name"]
        if not slug or slug in seen_slugs:
            continue
        seen_slugs.add(slug)
        items = queryset.filter(genres__slug=slug).distinct()[:limit]
        if not items:
            continue
        genres.append(
            {
                "slug": slug,
                "title": title,
                "description": "Локальная fallback-полка из текущей базы.",
                "media_type": _resolve_section_media_type(items),
                "items": _serialize_movie_queryset(items),
                "sort_order": sort_order,
            }
        )
        sort_order += 1
        if len(genres) >= 6:
            break

    featured = (
        weekly_top[Movie.MediaType.MOVIE][:1]
        or weekly_top[Movie.MediaType.ANIME][:1]
        or weekly_top[Movie.MediaType.SERIES][:1]
    )

    return {
        "featured": featured[0] if featured else None,
        "weekly_top": weekly_top,
        "genres": genres,
        "last_refreshed_for": None,
        "last_completed_at": None,
        "stale": True,
    }


def _persist_sections(section_payloads: Iterable[dict]) -> dict:
    section_payloads = list(section_payloads)
    active_slugs = [payload["slug"] for payload in section_payloads]
    summary = {"sections": {}, "total_movies": 0}

    with transaction.atomic():
        ShowcaseSection.objects.exclude(slug__in=active_slugs).update(is_active=False)

        for payload in section_payloads:
            section, _ = ShowcaseSection.objects.update_or_create(
                slug=payload["slug"],
                defaults={
                    "title": payload["title"],
                    "description": payload.get("description", ""),
                    "section_type": payload["section_type"],
                    "media_type": payload["media_type"],
                    "sort_order": payload["sort_order"],
                    "is_active": True,
                    "metadata": {"source": "tmdb", "items_count": len(payload["items"])},
                },
            )
            previous_ranks = {
                item.movie.tmdb_id: item.rank
                for item in section.items.select_related("movie")
            }
            section.items.all().delete()
            created_items = []

            for rank, item in enumerate(payload["items"], start=1):
                movie = sync_movie_from_tmdb(item["tmdb_id"], media_type=item["media_type"])
                previous_rank = previous_ranks.get(movie.tmdb_id)
                movement, delta = _movement(previous_rank, rank)
                created_items.append(
                    ShowcaseSectionItem(
                        section=section,
                        movie=movie,
                        rank=rank,
                        previous_rank=previous_rank,
                        movement=movement,
                        delta=delta,
                        metadata={
                            "source": "tmdb",
                            "source_vote_average": item.get("tmdb_vote_average"),
                        },
                    )
                )

            ShowcaseSectionItem.objects.bulk_create(created_items)
            summary["sections"][section.slug] = {
                "count": len(created_items),
                "new": sum(1 for item in created_items if item.movement == ShowcaseSectionItem.Movement.NEW),
                "up": sum(1 for item in created_items if item.movement == ShowcaseSectionItem.Movement.UP),
                "down": sum(1 for item in created_items if item.movement == ShowcaseSectionItem.Movement.DOWN),
            }
            summary["total_movies"] += len(created_items)

    return summary


def _movement(previous_rank: int | None, current_rank: int) -> tuple[str, int]:
    if previous_rank is None:
        return ShowcaseSectionItem.Movement.NEW, 0
    if previous_rank == current_rank:
        return ShowcaseSectionItem.Movement.SAME, 0
    if previous_rank > current_rank:
        return ShowcaseSectionItem.Movement.UP, previous_rank - current_rank
    return ShowcaseSectionItem.Movement.DOWN, current_rank - previous_rank


def _serialize_showcase_item(item: ShowcaseSectionItem) -> dict:
    return {
        **_serialize_movie(item.movie),
        "rank": item.rank,
        "previous_rank": item.previous_rank,
        "movement": item.movement,
        "delta": item.delta,
    }


def _serialize_movie_queryset(queryset) -> list[dict]:
    return [_serialize_movie(movie) for movie in queryset]


def _serialize_movie(movie: Movie) -> dict:
    tmdb_vote_average = movie.tmdb_vote_average
    return {
        "tmdb_id": movie.tmdb_id,
        "local_id": movie.id,
        "media_type": movie.media_type,
        "title": movie.title,
        "original_title": movie.original_title,
        "description": movie.description,
        "release_year": movie.release_year,
        "poster_url": movie.poster_url,
        "backdrop_url": movie.backdrop_url,
        "tmdb_vote_average": float(tmdb_vote_average) if tmdb_vote_average is not None else None,
    }


def _resolve_section_media_type(items) -> str:
    media_types = {item.media_type for item in items}
    if len(media_types) == 1:
        return next(iter(media_types))
    return ShowcaseSection.MediaTypeFilter.MIXED
