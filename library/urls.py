from django.urls import path

from . import views


urlpatterns = [

    # ========================================================
    # WATCHLIST
    # ========================================================

    path(
        "watchlist/",
        views.watchlist_view,
        name="watchlist",
    ),

    path(
        "watchlist/movie/<int:movie_id>/add/",
        views.add_movie_to_watchlist,
        name="add-movie-watchlist",
    ),

    path(
        "watchlist/movie/<int:movie_id>/remove/",
        views.remove_movie_from_watchlist,
        name="remove-movie-watchlist",
    ),

    path(
        "watchlist/tv/<int:tv_show_id>/add/",
        views.add_tv_to_watchlist,
        name="add-tv-watchlist",
    ),

    path(
        "watchlist/tv/<int:tv_show_id>/remove/",
        views.remove_tv_from_watchlist,
        name="remove-tv-watchlist",
    ),


    # ========================================================
    # COLLECTIONS
    # ========================================================

    path(
        "collections/",
        views.collection_list_view,
        name="collection-list",
    ),

    path(
        "collections/create/",
        views.create_collection_view,
        name="create-collection",
    ),

    path(
        "collections/<int:collection_id>/",
        views.collection_detail_view,
        name="collection-detail",
    ),

    path(
        "collections/<int:collection_id>/edit/",
        views.edit_collection_view,
        name="edit-collection",
    ),

    path(
        "collections/<int:collection_id>/delete/",
        views.delete_collection_view,
        name="delete-collection",
    ),


    # ========================================================
    # MOVIES IN COLLECTIONS
    # ========================================================

    path(
        "collections/<int:collection_id>/movie/<int:movie_id>/add/",
        views.add_movie_to_collection,
        name="add-movie-collection",
    ),

    path(
        "collections/<int:collection_id>/movie/<int:movie_id>/remove/",
        views.remove_movie_from_collection,
        name="remove-movie-collection",
    ),


    # ========================================================
    # TV SHOWS IN COLLECTIONS
    # ========================================================

    path(
        "collections/<int:collection_id>/tv/<int:tv_show_id>/add/",
        views.add_tv_to_collection,
        name="add-tv-collection",
    ),

    path(
        "collections/<int:collection_id>/tv/<int:tv_show_id>/remove/",
        views.remove_tv_from_collection,
        name="remove-tv-collection",
    ),


    # ========================================================
    # MOVIE COLLECTION SELECTOR
    # ========================================================

    path(
        "movie/<int:movie_id>/collections/",
        views.movie_collection_selector,
        name="movie-collection-selector",
    ),


    # ========================================================
    # TV SHOW COLLECTION SELECTOR
    # ========================================================

    path(
        "tv/<int:tv_show_id>/collections/",
        views.tv_collection_selector,
        name="tv-collection-selector",
    ),


    # ========================================================
    # OTHER USER'S PUBLIC COLLECTIONS
    # ========================================================

    path(
        "user/<str:username>/collections/",
        views.user_collections_view,
        name="user-collections",
    ),
]