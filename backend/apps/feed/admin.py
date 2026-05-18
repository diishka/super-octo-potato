from django.contrib import admin

from .models import Activity, ActivityComment, ActivityLike


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ("user", "activity_type", "movie", "created_at")
    list_filter = ("activity_type",)
    search_fields = ("user__username", "movie__title")


@admin.register(ActivityLike)
class ActivityLikeAdmin(admin.ModelAdmin):
    list_display = ("user", "activity", "created_at")


@admin.register(ActivityComment)
class ActivityCommentAdmin(admin.ModelAdmin):
    list_display = ("user", "activity", "created_at")
    search_fields = ("user__username", "text")
