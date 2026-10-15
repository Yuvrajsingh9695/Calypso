
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from comments.models import Comment
from library.models import WatchlistItem

from .filters import clean_tv_queryset
from .models import TVShow
from .recommendations import get_similar_tv_shows


def tv_home(request):
    base_queryset = clean_tv_queryset(
        TVShow.objects.filter(
            poster_path__isnull=False,
        ).exclude(
            poster_path=""
        )
    )

    latest_shows = base_queryset.filter(
        first_air_date__isnull=False,
    ).order_by(
        "-first_air_date"
    )[:12]

    latest_ids = latest_shows.values_list(
        "tmdb_id",
        flat=True,
    )

    top_rated_shows = (
        base_queryset.exclude(
            tmdb_id__in=latest_ids
        )
        .filter(vote_count__gte=40)
        .order_by(
            "-vote_average",
            "-vote_count",
        )[:12]
    )

    return render(
        request,
        "tvshows/index.html",
        {
            "latest_shows": latest_shows,
            "top_rated_shows": top_rated_shows,
        },
    )


def tv_list(request, page=1):
    query = request.GET.get("q", "").strip()

    shows = clean_tv_queryset(
        TVShow.objects.all()
    )

    if query:
        shows = shows.filter(
            Q(name__icontains=query)
            | Q(original_name__icontains=query)
        )

    shows = shows.order_by("-first_air_date")

    paginator = Paginator(shows, 24)
    page_obj = paginator.get_page(page)

    return render(
        request,
        "tvshows/tv_list.html",
        {
            "shows": page_obj.object_list,
            "page_obj": page_obj,
            "page": page_obj.number,
            "total_pages": paginator.num_pages,
            "query": query,
        },
    )


def tv_detail(request, show_id):
    # show = get_object_or_404(
    #     clean_tv_queryset(TVShow.objects.all()),
    #     tmdb_id=show_id,
    # )
    show = get_object_or_404(
    TVShow.objects.all(),
    tmdb_id=show_id,
)

    comments = (
        Comment.objects.filter(
            tv_show=show,
            parent__isnull=True,
        )
        .select_related("user")
        .prefetch_related(
            "replies__user",
            "likes",
        )
    )

    in_watchlist = False

    if request.user.is_authenticated:
        in_watchlist = WatchlistItem.objects.filter(
            watchlist__user=request.user,
            tv_show=show,
        ).exists()

    try:
        similar_shows = get_similar_tv_shows(
            show,
            limit=10,
        )
    except (
        FileNotFoundError,
        ImportError,
        OSError,
        ValueError,
    ):
        similar_shows = []

    return render(
        request,
        "tvshows/tv_detail.html",
        {
            "show": show,
            "comments": comments,
            "comment_form_url": reverse(
                "add_tv_comment",
                args=[show.id],
            ),
            "in_watchlist": in_watchlist,
            "similar_shows": similar_shows,
        },
    )


def genre_shows(request, genre):
    shows = clean_tv_queryset(
        TVShow.objects.filter(
            genres__icontains=genre,
        )
    ).order_by(
        "-first_air_date"
    )

    paginator = Paginator(shows, 24)

    page_obj = paginator.get_page(
        request.GET.get("page", 1)
    )

    return render(
        request,
        "tvshows/tv_list.html",
        {
            "shows": page_obj.object_list,
            "page_obj": page_obj,
            "page": page_obj.number,
            "total_pages": paginator.num_pages,
            "query": "",
            "genre": genre,
        },
    )
