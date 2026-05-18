from django.contrib import admin

from .models import (
    Genre,
    LinkVote,
    Movie,
    MovieLink,
    ShowcaseRefreshState,
    ShowcaseSection,
    ShowcaseSectionItem,
    UserMovie,
)


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name",)


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ("title", "media_type", "release_year", "tmdb_id")
    list_filter = ("media_type", "release_year")
    search_fields = ("title", "original_title")


@admin.register(UserMovie)
class UserMovieAdmin(admin.ModelAdmin):
    list_display = ("user", "movie", "status", "rating", "recommended_to_followers")
    list_filter = ("status", "recommended_to_followers")
    search_fields = ("user__username", "movie__title")


@admin.register(MovieLink)
class MovieLinkAdmin(admin.ModelAdmin):
    list_display = ("movie", "source_name", "added_by", "created_at")
    search_fields = ("movie__title", "source_name", "url")


@admin.register(LinkVote)
class LinkVoteAdmin(admin.ModelAdmin):
    list_display = ("user", "link", "value", "updated_at")


class ShowcaseSectionItemInline(admin.TabularInline):
    model = ShowcaseSectionItem
    extra = 0
    autocomplete_fields = ("movie",)


@admin.register(ShowcaseSection)
class ShowcaseSectionAdmin(admin.ModelAdmin):
    list_display = ("title", "section_type", "media_type", "sort_order", "refreshed_at")
    list_filter = ("section_type", "media_type", "is_active")
    search_fields = ("title", "slug")
    inlines = [ShowcaseSectionItemInline]


@admin.register(ShowcaseRefreshState)
class ShowcaseRefreshStateAdmin(admin.ModelAdmin):
    list_display = ("key", "last_refreshed_for", "last_status", "last_completed_at")
    readonly_fields = (
        "key",
        "last_refreshed_for",
        "last_started_at",
        "last_completed_at",
        "last_status",
        "last_error",
        "payload_summary",
        "updated_at",
    )
