from django.conf import settings
from django.db import models


class Comment(models.Model):
    season_number = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
    )

    episode_number = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
    )

    # ========================================================
    # USER
    # ========================================================

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="comments",
    )

    # ========================================================
    # MOVIE
    # ========================================================

    movie = models.ForeignKey(
        "movies.Movie",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="comments",
    )

    # ========================================================
    # TV SHOW
    # ========================================================

    tv_show = models.ForeignKey(
        "tvshows.TVShow",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="comments",
    )

    # ========================================================
    # SEASON AND EPISODE IDENTIFIERS
    # ========================================================

    season_number = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="TMDB season number. Null for general TV show comments.",
    )

    episode_number = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="TMDB episode number. Null for season-level comments.",
    )

    # ========================================================
    # REPLIES
    # ========================================================

    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="replies",
    )

    # ========================================================
    # COMMENT CONTENT
    # ========================================================

    content = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    # ========================================================
    # LIKES
    # ========================================================

    likes = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="liked_comments",
        blank=True,
    )

    # ========================================================
    # DATABASE CONFIGURATION
    # ========================================================

    class Meta:
        ordering = ["-created_at"]

        indexes = [
            models.Index(
                fields=[
                    "tv_show",
                    "season_number",
                    "episode_number",
                ],
                name="comment_tv_scope_idx",
            ),
        ]

    # ========================================================
    # STRING REPRESENTATION
    # ========================================================

    def __str__(self):
        return f"{self.user} - {self.content[:50]}"

    # ========================================================
    # LIKE COUNT
    # ========================================================

    @property
    def like_count(self):
        return self.likes.count()

    # ========================================================
    # REPLY COUNT
    # ========================================================

    @property
    def reply_count(self):
        return self.replies.count()

    # ========================================================
    # COMMENT TYPE
    # ========================================================

    @property
    def comment_type(self):

        if self.movie_id:
            return "movie"

        if self.tv_show_id:

            if self.episode_number is not None:
                return "episode"

            if self.season_number is not None:
                return "season"

            return "tv_show"

        return "unknown"
