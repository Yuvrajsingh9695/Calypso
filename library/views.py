from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from movies.models import Movie
from tvshows.models import TVShow
from users.models import User

from .models import (
    Collection,
    CollectionItem,
    Watchlist,
    WatchlistItem,
)


# ============================================================
# WATCHLIST HELPER
# ============================================================


def get_user_watchlist(user):
    watchlist, created = Watchlist.objects.get_or_create(
        user=user
    )

    return watchlist


# ============================================================
# WATCHLIST
# ============================================================


@login_required
def watchlist_view(request):

    watchlist = get_user_watchlist(request.user)

    items = (
        watchlist.items
        .select_related("movie", "tv_show")
        .order_by("-added_at")
    )

    return render(
        request,
        "library/watchlist.html",
        {
            "watchlist": watchlist,
            "items": items,
        },
    )


# ============================================================
# ADD MOVIE TO WATCHLIST
# ============================================================


@login_required
def add_movie_to_watchlist(request, movie_id):

    if request.method != "POST":
        return redirect(
            "movie-detail",
            movie_id=movie_id
        )

    movie = get_object_or_404(
        Movie,
        tmdb_id=movie_id
    )

    watchlist = get_user_watchlist(
        request.user
    )

    item, created = WatchlistItem.objects.get_or_create(
        watchlist=watchlist,
        movie=movie
    )

    if created:

        messages.success(
            request,
            f'"{movie.title}" was added to your watchlist.'
        )

    else:

        messages.info(
            request,
            f'"{movie.title}" is already in your watchlist.'
        )

    return redirect(
        "movie-detail",
        movie_id=movie.tmdb_id
    )


# ============================================================
# REMOVE MOVIE FROM WATCHLIST
# ============================================================


@login_required
def remove_movie_from_watchlist(request, movie_id):

    if request.method != "POST":
        return redirect(
            "movie-detail",
            movie_id=movie_id
        )

    movie = get_object_or_404(
        Movie,
        tmdb_id=movie_id
    )

    watchlist = get_user_watchlist(
        request.user
    )

    WatchlistItem.objects.filter(
        watchlist=watchlist,
        movie=movie
    ).delete()

    messages.success(
        request,
        f'"{movie.title}" was removed from your watchlist.'
    )

    return redirect(
        "movie-detail",
        movie_id=movie.tmdb_id
    )


# ============================================================
# ADD TV SHOW TO WATCHLIST
# ============================================================


@login_required
def add_tv_to_watchlist(request, tv_show_id):

    if request.method != "POST":
        return redirect(
            request.META.get(
                "HTTP_REFERER",
                "watchlist"
            )
        )

    tv_show = get_object_or_404(
        TVShow,
        id=tv_show_id
    )

    watchlist = get_user_watchlist(
        request.user
    )

    item, created = WatchlistItem.objects.get_or_create(
        watchlist=watchlist,
        tv_show=tv_show
    )

    if created:

        messages.success(
            request,
            f'"{tv_show.name}" was added to your watchlist.'
        )

    else:

        messages.info(
            request,
            f'"{tv_show.name}" is already in your watchlist.'
        )

    return redirect(
        request.META.get(
            "HTTP_REFERER",
            "watchlist"
        )
    )


# ============================================================
# REMOVE TV SHOW FROM WATCHLIST
# ============================================================


@login_required
def remove_tv_from_watchlist(request, tv_show_id):

    if request.method != "POST":
        return redirect(
            request.META.get(
                "HTTP_REFERER",
                "watchlist"
            )
        )

    tv_show = get_object_or_404(
        TVShow,
        id=tv_show_id
    )

    watchlist = get_user_watchlist(
        request.user
    )

    WatchlistItem.objects.filter(
        watchlist=watchlist,
        tv_show=tv_show
    ).delete()

    messages.success(
        request,
        f'"{tv_show.name}" was removed from your watchlist.'
    )

    return redirect(
        request.META.get(
            "HTTP_REFERER",
            "watchlist"
        )
    )


# ============================================================
# COLLECTION LIST
# ============================================================


@login_required
def collection_list_view(request):

    collections = (
        Collection.objects
        .filter(user=request.user)
        .prefetch_related("items")
    )

    return render(
        request,
        "library/collections.html",
        {
            "collections": collections,
        },
    )


# ============================================================
# CREATE COLLECTION
# ============================================================


@login_required
def create_collection_view(request):

    if request.method == "POST":

        name = request.POST.get(
            "name",
            ""
        ).strip()

        description = request.POST.get(
            "description",
            ""
        ).strip()

        is_public = (
            request.POST.get("is_public")
            == "on"
        )

        if not name:

            messages.error(
                request,
                "Collection name cannot be empty."
            )

            return redirect(
                "create-collection"
            )

        collection = Collection.objects.create(
            user=request.user,
            name=name,
            description=description,
            is_public=is_public,
        )

        messages.success(
            request,
            f'Collection "{collection.name}" created.'
        )

        return redirect(
            "collection-detail",
            collection_id=collection.id
        )

    return render(
        request,
        "library/create_collection.html"
    )


# ============================================================
# COLLECTION DETAIL
# ============================================================


@login_required
def collection_detail_view(request, collection_id):

    collection = get_object_or_404(
        Collection,
        id=collection_id
    )

    if (
        collection.user != request.user
        and not collection.is_public
    ):

        messages.error(
            request,
            "This collection is private."
        )

        return redirect(
            "collection-list"
        )

    items = (
        collection.items
        .select_related(
            "movie",
            "tv_show"
        )
        .order_by("-added_at")
    )

    return render(
        request,
        "library/collection_detail.html",
        {
            "collection": collection,
            "items": items,
        },
    )


# ============================================================
# EDIT COLLECTION
# ============================================================


@login_required
def edit_collection_view(request, collection_id):

    collection = get_object_or_404(
        Collection,
        id=collection_id,
        user=request.user
    )

    if request.method == "POST":

        name = request.POST.get(
            "name",
            ""
        ).strip()

        description = request.POST.get(
            "description",
            ""
        ).strip()

        is_public = (
            request.POST.get("is_public")
            == "on"
        )

        if not name:

            messages.error(
                request,
                "Collection name cannot be empty."
            )

            return redirect(
                "edit-collection",
                collection_id=collection.id
            )

        collection.name = name
        collection.description = description
        collection.is_public = is_public

        collection.save()

        messages.success(
            request,
            "Collection updated successfully."
        )

        return redirect(
            "collection-detail",
            collection_id=collection.id
        )

    return render(
        request,
        "library/edit_collection.html",
        {
            "collection": collection,
        },
    )


# ============================================================
# DELETE COLLECTION
# ============================================================


@login_required
def delete_collection_view(request, collection_id):

    collection = get_object_or_404(
        Collection,
        id=collection_id,
        user=request.user
    )

    if request.method == "POST":

        collection_name = collection.name

        collection.delete()

        messages.success(
            request,
            f'Collection "{collection_name}" deleted.'
        )

        return redirect(
            "collection-list"
        )

    return redirect(
        "collection-detail",
        collection_id=collection.id
    )


# ============================================================
# ADD MOVIE TO COLLECTION
# ============================================================


@login_required
def add_movie_to_collection(
    request,
    collection_id,
    movie_id
):

    if request.method != "POST":
        return redirect(
            "collection-detail",
            collection_id=collection_id
        )

    collection = get_object_or_404(
        Collection,
        id=collection_id,
        user=request.user
    )

    movie = get_object_or_404(
        Movie,
        tmdb_id=movie_id
    )

    item, created = CollectionItem.objects.get_or_create(
        collection=collection,
        movie=movie
    )

    if created:

        messages.success(
            request,
            f'"{movie.title}" added to "{collection.name}".'
        )

    else:

        messages.info(
            request,
            f'"{movie.title}" is already in "{collection.name}".'
        )

    return redirect(
        "collection-detail",
        collection_id=collection.id
    )


# ============================================================
# REMOVE MOVIE FROM COLLECTION
# ============================================================


@login_required
def remove_movie_from_collection(
    request,
    collection_id,
    movie_id
):

    if request.method != "POST":
        return redirect(
            "collection-detail",
            collection_id=collection_id
        )

    collection = get_object_or_404(
        Collection,
        id=collection_id,
        user=request.user
    )

    movie = get_object_or_404(
        Movie,
        tmdb_id=movie_id
    )

    CollectionItem.objects.filter(
        collection=collection,
        movie=movie
    ).delete()

    messages.success(
        request,
        f'"{movie.title}" removed from "{collection.name}".'
    )

    return redirect(
        "collection-detail",
        collection_id=collection.id
    )


# ============================================================
# ADD TV SHOW TO COLLECTION
# ============================================================


@login_required
def add_tv_to_collection(
    request,
    collection_id,
    tv_show_id
):

    if request.method != "POST":
        return redirect(
            "collection-detail",
            collection_id=collection_id
        )

    collection = get_object_or_404(
        Collection,
        id=collection_id,
        user=request.user
    )

    tv_show = get_object_or_404(
        TVShow,
        id=tv_show_id
    )

    item, created = CollectionItem.objects.get_or_create(
        collection=collection,
        tv_show=tv_show
    )

    if created:

        messages.success(
            request,
            f'"{tv_show.name}" added to "{collection.name}".'
        )

    else:

        messages.info(
            request,
            f'"{tv_show.name}" is already in "{collection.name}".'
        )

    return redirect(
        "collection-detail",
        collection_id=collection.id
    )


# ============================================================
# REMOVE TV SHOW FROM COLLECTION
# ============================================================


@login_required
def remove_tv_from_collection(
    request,
    collection_id,
    tv_show_id
):

    if request.method != "POST":
        return redirect(
            "collection-detail",
            collection_id=collection_id
        )

    collection = get_object_or_404(
        Collection,
        id=collection_id,
        user=request.user
    )

    tv_show = get_object_or_404(
        TVShow,
        id=tv_show_id
    )

    CollectionItem.objects.filter(
        collection=collection,
        tv_show=tv_show
    ).delete()

    messages.success(
        request,
        f'"{tv_show.name}" removed from "{collection.name}".'
    )

    return redirect(
        "collection-detail",
        collection_id=collection.id
    )


# ============================================================
# MOVIE COLLECTION SELECTOR
# ============================================================


@login_required
def movie_collection_selector(
    request,
    movie_id
):

    movie = get_object_or_404(
        Movie,
        tmdb_id=movie_id
    )

    collections = Collection.objects.filter(
        user=request.user
    )

    return render(
        request,
        "library/movie_collection_selector.html",
        {
            "movie": movie,
            "collections": collections,
        },
    )


# ============================================================
# TV SHOW COLLECTION SELECTOR
# ============================================================


@login_required
def tv_collection_selector(
    request,
    tv_show_id
):

    tv_show = get_object_or_404(
        TVShow,
        id=tv_show_id
    )

    collections = Collection.objects.filter(
        user=request.user
    )

    return render(
        request,
        "library/tv_collection_selector.html",
        {
            "tv_show": tv_show,
            "collections": collections,
        },
    )


# ============================================================
# USER PUBLIC COLLECTIONS
# ============================================================


@login_required
def user_collections_view(
    request,
    username
):

    profile_user = get_object_or_404(
        User,
        username=username
    )

    collections = (
        Collection.objects
        .filter(
            user=profile_user,
            is_public=True
        )
        .prefetch_related("items")
    )

    return render(
        request,
        "library/user_collections.html",
        {
            "profile_user": profile_user,
            "collections": collections,
        },
    )