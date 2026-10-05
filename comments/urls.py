from django.urls import path

from . import views


urlpatterns = [

    # ========================================================
    # MOVIE COMMENTS
    # ========================================================

    path(
        "movie/<int:movie_id>/add/",
        views.add_movie_comment,
        name="add_movie_comment",
    ),


    # ========================================================
    # TV SHOW COMMENTS
    # ========================================================

    path(
        "tv/<int:tv_show_id>/add/",
        views.add_tv_comment,
        name="add_tv_comment",
    ),


    # ========================================================
    # COMMENT REPLIES
    # ========================================================

    path(
        "reply/<int:comment_id>/",
        views.reply_comment,
        name="reply_comment",
    ),


    # ========================================================
    # COMMENT LIKE
    # ========================================================

    path(
        "like/<int:comment_id>/",
        views.like_comment,
        name="like_comment",
    ),


    # ========================================================
    # DELETE COMMENT
    # ========================================================

    path(
        "delete/<int:comment_id>/",
        views.delete_comment,
        name="delete_comment",
    ),
]