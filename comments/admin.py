from django.contrib import admin
from .models import Comment


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "user",
        "movie",
        "tv_show",
        "parent",
        "created_at",
        "like_count",
    )

    list_filter = ("created_at",)

    search_fields = (
        "content",
        "user__username",
    )
