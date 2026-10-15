from datetime import timedelta

from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count
from django.shortcuts import render
from django.utils import timezone

from users.models import User
from movies.models import Movie
from tvshows.models import TVShow
from comments.models import Comment
from library.models import (
    Watchlist,
    WatchlistItem,
    Collection,
    CollectionItem,
)


@staff_member_required
def dashboard(request):
    today = timezone.localdate()
    month_start = today.replace(day=1)
    tomorrow = today + timedelta(days=1)

    # User statistics
    total_users = User.objects.count()

    new_users_today = User.objects.filter(date_joined__date=today).count()

    new_users_month = User.objects.filter(
        date_joined__date__gte=month_start,
        date_joined__date__lt=tomorrow,
    ).count()

    # Movie statistics
    total_movies = Movie.objects.count()

    new_movies_today = Movie.objects.filter(created_at__date=today).count()

    new_movies_month = Movie.objects.filter(
        created_at__date__gte=month_start,
        created_at__date__lt=tomorrow,
    ).count()

    # TV show statistics
    total_shows = TVShow.objects.count()

    new_shows_today = TVShow.objects.filter(created_at__date=today).count()

    new_shows_month = TVShow.objects.filter(
        created_at__date__gte=month_start,
        created_at__date__lt=tomorrow,
    ).count()

    # Comment and engagement statistics
    total_comments = Comment.objects.count()

    total_replies = Comment.objects.filter(parent__isnull=False).count()

    new_comments_today = Comment.objects.filter(created_at__date=today).count()

    total_comment_likes = sum(
        comment.likes.count() for comment in Comment.objects.prefetch_related("likes")
    )

    # Watchlist and collection statistics
    total_watchlists = Watchlist.objects.count()
    total_watchlist_items = WatchlistItem.objects.count()

    total_collections = Collection.objects.count()

    public_collections = Collection.objects.filter(is_public=True).count()

    total_collection_items = CollectionItem.objects.count()

    # Following statistics
    total_follow_relationships = sum(
        user.following.count() for user in User.objects.prefetch_related("following")
    )

    # Monthly chart: current month and previous 5 months
    monthly_labels = []
    monthly_users = []
    monthly_movies = []
    monthly_shows = []

    for offset in range(5, -1, -1):
        month_number = today.month - offset
        year = today.year

        while month_number <= 0:
            month_number += 12
            year -= 1

        start = today.replace(
            year=year,
            month=month_number,
            day=1,
        )

        if month_number == 12:
            end = start.replace(
                year=year + 1,
                month=1,
                day=1,
            )
        else:
            end = start.replace(
                month=month_number + 1,
                day=1,
            )

        monthly_labels.append(start.strftime("%b %Y"))

        monthly_users.append(
            User.objects.filter(
                date_joined__date__gte=start,
                date_joined__date__lt=end,
            ).count()
        )

        monthly_movies.append(
            Movie.objects.filter(
                created_at__date__gte=start,
                created_at__date__lt=end,
            ).count()
        )

        monthly_shows.append(
            TVShow.objects.filter(
                created_at__date__gte=start,
                created_at__date__lt=end,
            ).count()
        )

    # Content highlights
    popular_movies = Movie.objects.order_by("-popularity")[:5]

    popular_shows = TVShow.objects.order_by("-popularity")[:5]

    context = {
        "report_date": today,
        "total_users": total_users,
        "new_users_today": new_users_today,
        "new_users_month": new_users_month,
        "total_movies": total_movies,
        "new_movies_today": new_movies_today,
        "new_movies_month": new_movies_month,
        "total_shows": total_shows,
        "new_shows_today": new_shows_today,
        "new_shows_month": new_shows_month,
        "total_comments": total_comments,
        "total_replies": total_replies,
        "new_comments_today": new_comments_today,
        "total_comment_likes": total_comment_likes,
        "total_watchlists": total_watchlists,
        "total_watchlist_items": total_watchlist_items,
        "total_collections": total_collections,
        "public_collections": public_collections,
        "total_collection_items": total_collection_items,
        "total_follow_relationships": total_follow_relationships,
        "monthly_labels": monthly_labels,
        "monthly_users": monthly_users,
        "monthly_movies": monthly_movies,
        "monthly_shows": monthly_shows,
        "popular_movies": popular_movies,
        "popular_shows": popular_shows,
    }

    return render(
        request,
        "analytics/dashboard.html",
        context,
    )
