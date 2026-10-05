from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from comments.models import Comment
from library.models import WatchlistItem

from .models import TVShow


# ============================================================
# TV CONTENT FILTER
# ============================================================

MIN_TV_VOTES = 1000

def clean_tv_queryset(queryset):

    MIN_VOTE_COUNT = 1000

    queryset = queryset.filter(
        vote_count__gte=MIN_VOTE_COUNT,
        is_adult=False,
    )

    blocked_terms = [
        "hentai",
        "ecchi",
        "porn",
        "pornographic",
        "sexually explicit",
        "explicit sexual",
        "adult animation",
        "adult anime",
        "erotic animation",
        "erotic anime",
        "erotic",
        "xxx",
        "sexual content",
        "sexual intercourse",
        "sex slave",
        "sex slavery",
        "incest",
        "nudity",
        "sexual violence",
    ]

    for term in blocked_terms:
        queryset = queryset.exclude(
            Q(name__icontains=term)
            | Q(original_name__icontains=term)
            | Q(overview__icontains=term)
            | Q(genres__icontains=term)
        )

    return queryset


# ============================================================
# TV HOME
# ============================================================

def tv_home(request):

    # --------------------------------------------------------
    # LATEST TV SHOWS
    # --------------------------------------------------------

    latest_shows = clean_tv_queryset(
        TVShow.objects.filter(
            first_air_date__isnull=False,
            poster_path__isnull=False,
        ).exclude(
            poster_path=""
        )
    ).order_by(
        "-first_air_date"
    )[:12]

    # IDs already shown in Latest
    latest_ids = latest_shows.values_list(
        "tmdb_id",
        flat=True
    )

    # --------------------------------------------------------
    # POPULAR TV SHOWS
    # --------------------------------------------------------

    popular_shows = clean_tv_queryset(
        TVShow.objects.filter(
            poster_path__isnull=False,
        )
        .exclude(
            poster_path=""
        )
        .exclude(
            tmdb_id__in=latest_ids
        )
    ).order_by(
        "-popularity"
    )[:12]

    return render(
        request,
        "tvshows/index.html",
        {
            "latest_shows": latest_shows,
            "popular_shows": popular_shows,
        },
    )


# ============================================================
# TV SHOW LIST + SEARCH
# ============================================================

def tv_list(request, page=1):

    query = request.GET.get(
        "q",
        ""
    ).strip()

    # IMPORTANT:
    # Start with ALL TV shows and then apply the central filter.
    shows = clean_tv_queryset(
        TVShow.objects.all()
    )

    # --------------------------------------------------------
    # SEARCH
    # --------------------------------------------------------

    if query:

        shows = shows.filter(
            Q(name__icontains=query)
            |
            Q(original_name__icontains=query)
        )

    # --------------------------------------------------------
    # ORDER
    # --------------------------------------------------------

    shows = shows.order_by(
        "-first_air_date"
    )

    # --------------------------------------------------------
    # PAGINATION
    # --------------------------------------------------------

    paginator = Paginator(
        shows,
        24
    )

    page_obj = paginator.get_page(
        page
    )

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


# ============================================================
# TV DETAIL
# ============================================================

def tv_detail(request, show_id):

    show = get_object_or_404(
        TVShow,
        tmdb_id=show_id
    )

    comments = (
        Comment.objects
        .filter(
            tv_show=show,
            parent__isnull=True
        )
        .select_related(
            "user"
        )
        .prefetch_related(
            "replies__user",
            "likes"
        )
    )

    # --------------------------------------------------------
    # WATCHLIST STATUS
    # --------------------------------------------------------

    in_watchlist = False

    if request.user.is_authenticated:

        in_watchlist = WatchlistItem.objects.filter(
            watchlist__user=request.user,
            tv_show=show,
        ).exists()

    return render(
        request,
        "tvshows/tv_detail.html",
        {
            "show": show,

            "comments": comments,

            "comment_form_url": reverse(
                "add_tv_comment",
                args=[show.id]
            ),

            "in_watchlist": in_watchlist,
        },
    )


# ============================================================
# TV GENRE
# ============================================================

def genre_shows(request, genre):

    # IMPORTANT:
    # Genre pages also go through the SAME filter.
    shows = clean_tv_queryset(
        TVShow.objects.filter(
            genres__icontains=genre
        )
    ).order_by(
        "-first_air_date"
    )

    paginator = Paginator(
        shows,
        24
    )

    page_obj = paginator.get_page(
        request.GET.get(
            "page",
            1
        )
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