from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Profile", {"fields": ("bio", "avatar_url", "watched_count", "wishlist_count")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Profile", {"fields": ("email", "bio", "avatar_url")}),
    )
    list_display = ("username", "email", "is_staff", "watched_count", "wishlist_count")
