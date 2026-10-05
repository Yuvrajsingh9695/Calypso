from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string

from .models import Comment

from movies.models import Movie
from tvshows.models import TVShow


# ============================================================
# HELPER: GET COMMENTS
# ============================================================

def get_comments_for_movie(movie):
    return (
        Comment.objects
        .filter(
            movie=movie,
            parent__isnull=True
        )
        .select_related("user")
        .prefetch_related(
            "replies__user",
            "likes",
            "replies__likes",
        )
    )


def get_comments_for_tv_show(tv_show):
    return (
        Comment.objects
        .filter(
            tv_show=tv_show,
            parent__isnull=True
        )
        .select_related("user")
        .prefetch_related(
            "replies__user",
            "likes",
            "replies__likes",
        )
    )


# ============================================================
# HELPER: RENDER COMMENT LIST
# ============================================================

def render_comment_list(request, comments):

    html = render_to_string(
        "comments/comments_list.html",
        {
            "comments": comments,
            "user": request.user,
        },
        request=request,
    )

    return html


# ============================================================
# ADD MOVIE COMMENT
# ============================================================

@login_required
def add_movie_comment(request, movie_id):

    if request.method != "POST":
        return redirect("/")

    movie = get_object_or_404(
        Movie,
        id=movie_id
    )

    content = request.POST.get(
        "content",
        ""
    ).strip()

    if content:

        Comment.objects.create(
            user=request.user,
            movie=movie,
            content=content,
        )

    comments = get_comments_for_movie(movie)

    # AJAX request
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":

        return JsonResponse(
            {
                "success": True,
                "html": render_comment_list(
                    request,
                    comments
                ),
            }
        )

    # Normal request fallback
    return redirect(
        "movie-detail",
        movie_id=movie.tmdb_id
    )


# ============================================================
# ADD TV SHOW COMMENT
# ============================================================

@login_required
def add_tv_comment(request, tv_show_id):

    if request.method != "POST":
        return redirect("/")

    tv_show = get_object_or_404(
        TVShow,
        id=tv_show_id
    )

    content = request.POST.get(
        "content",
        ""
    ).strip()

    if content:

        Comment.objects.create(
            user=request.user,
            tv_show=tv_show,
            content=content,
        )

    comments = get_comments_for_tv_show(tv_show)

    # AJAX request
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":

        return JsonResponse(
            {
                "success": True,
                "html": render_comment_list(
                    request,
                    comments
                ),
            }
        )

    # Normal request fallback
    return redirect(
        request.META.get(
            "HTTP_REFERER",
            "/"
        )
    )


# ============================================================
# REPLY TO COMMENT
# ============================================================

@login_required
def reply_comment(request, comment_id):

    comment = get_object_or_404(
        Comment,
        id=comment_id
    )

    if request.method != "POST":

        return redirect(
            request.META.get(
                "HTTP_REFERER",
                "/"
            )
        )

    content = request.POST.get(
        "content",
        ""
    ).strip()

    if content:

        Comment.objects.create(
            user=request.user,
            movie=comment.movie,
            tv_show=comment.tv_show,
            parent=comment,
            content=content,
        )

    # Determine which page the comment belongs to
    if comment.movie:

        comments = get_comments_for_movie(
            comment.movie
        )

    elif comment.tv_show:

        comments = get_comments_for_tv_show(
            comment.tv_show
        )

    else:

        comments = Comment.objects.none()

    # AJAX request
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":

        return JsonResponse(
            {
                "success": True,
                "html": render_comment_list(
                    request,
                    comments
                ),
            }
        )

    return redirect(
        request.META.get(
            "HTTP_REFERER",
            "/"
        )
    )


# ============================================================
# LIKE / UNLIKE COMMENT
# ============================================================

@login_required
def like_comment(request, comment_id):

    comment = get_object_or_404(
        Comment,
        id=comment_id
    )

    if request.method != "POST":

        return redirect(
            request.META.get(
                "HTTP_REFERER",
                "/"
            )
        )

    if request.user in comment.likes.all():

        comment.likes.remove(
            request.user
        )

    else:

        comment.likes.add(
            request.user
        )

    # Determine parent comment list
    root_comment = comment

    if comment.parent:

        root_comment = comment.parent

    if root_comment.movie:

        comments = get_comments_for_movie(
            root_comment.movie
        )

    elif root_comment.tv_show:

        comments = get_comments_for_tv_show(
            root_comment.tv_show
        )

    else:

        comments = Comment.objects.none()

    # AJAX request
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":

        return JsonResponse(
            {
                "success": True,
                "html": render_comment_list(
                    request,
                    comments
                ),
            }
        )

    return redirect(
        request.META.get(
            "HTTP_REFERER",
            "/"
        )
    )


# ============================================================
# DELETE COMMENT
# ============================================================

@login_required
def delete_comment(request, comment_id):

    comment = get_object_or_404(
        Comment,
        id=comment_id
    )

    if comment.user != request.user:

        return HttpResponseForbidden(
            "You can only delete your own comments."
        )

    if request.method != "POST":

        return redirect(
            request.META.get(
                "HTTP_REFERER",
                "/"
            )
        )

    # Save the related object before deleting
    movie = comment.movie
    tv_show = comment.tv_show

    comment.delete()

    if movie:

        comments = get_comments_for_movie(
            movie
        )

    elif tv_show:

        comments = get_comments_for_tv_show(
            tv_show
        )

    else:

        comments = Comment.objects.none()

    # AJAX request
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":

        return JsonResponse(
            {
                "success": True,
                "html": render_comment_list(
                    request,
                    comments
                ),
            }
        )

    return redirect(
        request.META.get(
            "HTTP_REFERER",
            "/"
        )
    )