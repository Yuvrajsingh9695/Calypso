
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string

from .models import Comment

from movies.models import Movie
from tvshows.models import TVShow


# ============================================================
# HELPER: GET MOVIE COMMENTS
# ============================================================

def get_comments_for_movie(movie):
    return (
        Comment.objects
        .filter(
            movie=movie,
            parent__isnull=True,
        )
        .select_related("user")
        .prefetch_related(
            "replies__user",
            "likes",
            "replies__likes",
        )
    )


# ============================================================
# HELPER: GET TV COMMENTS BY SCOPE
# ============================================================

def get_comments_for_tv_scope(
    tv_show,
    season_number=None,
    episode_number=None,
):
    return (
        Comment.objects
        .filter(
            tv_show=tv_show,
            season_number=season_number,
            episode_number=episode_number,
            parent__isnull=True,
        )
        .select_related("user")
        .prefetch_related(
            "replies__user",
            "likes",
            "replies__likes",
        )
    )


# ============================================================
# HELPER: GET GENERAL TV SHOW COMMENTS
# ============================================================

def get_comments_for_tv_show(tv_show):
    return get_comments_for_tv_scope(
        tv_show=tv_show,
        season_number=None,
        episode_number=None,
    )


# ============================================================
# HELPER: FIND ROOT COMMENT
# ============================================================

def get_root_comment(comment):

    while comment.parent_id is not None:
        comment = comment.parent

    return comment


# ============================================================
# HELPER: GET CORRECT COMMENT LIST
# ============================================================

def get_comments_for_comment(comment):

    root_comment = get_root_comment(comment)

    if root_comment.movie_id:

        return get_comments_for_movie(
            root_comment.movie
        )

    elif root_comment.tv_show_id:

        return get_comments_for_tv_scope(
            tv_show=root_comment.tv_show,
            season_number=root_comment.season_number,
            episode_number=root_comment.episode_number,
        )

    return Comment.objects.none()


# ============================================================
# HELPER: RENDER COMMENT LIST
# ============================================================

def render_comment_list(request, comments):

    return render_to_string(
        "comments/comments_list.html",
        {
            "comments": comments,
            "user": request.user,
        },
        request=request,
    )


# ============================================================
# HELPER: COMMENT RESPONSE
# ============================================================

def comment_response(request, comments):

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":

        return JsonResponse(
            {
                "success": True,
                "html": render_comment_list(
                    request,
                    comments,
                ),
            }
        )

    return redirect(
        request.META.get(
            "HTTP_REFERER",
            "/",
        )
    )


# ============================================================
# ADD MOVIE COMMENT
# ============================================================

@login_required
def add_movie_comment(request, movie_id):

    if request.method != "POST":
        return redirect("/")

    movie = get_object_or_404(
        Movie,
        id=movie_id,
    )

    content = request.POST.get(
        "content",
        "",
    ).strip()

    if content:

        Comment.objects.create(
            user=request.user,
            movie=movie,
            content=content,
        )

    comments = get_comments_for_movie(movie)

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":

        return JsonResponse(
            {
                "success": True,
                "html": render_comment_list(
                    request,
                    comments,
                ),
            }
        )

    return redirect(
        "movie-detail",
        movie_id=movie.tmdb_id,
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
        id=tv_show_id,
    )

    content = request.POST.get(
        "content",
        "",
    ).strip()

    if content:

        Comment.objects.create(
            user=request.user,
            tv_show=tv_show,
            season_number=None,
            episode_number=None,
            content=content,
        )

    comments = get_comments_for_tv_show(tv_show)

    return comment_response(
        request,
        comments,
    )


# ============================================================
# ADD TV SEASON COMMENT
# ============================================================

@login_required
def add_tv_season_comment(
    request,
    tv_show_id,
    season_number,
):

    if request.method != "POST":
        return redirect("/")

    tv_show = get_object_or_404(
        TVShow,
        id=tv_show_id,
    )

    content = request.POST.get(
        "content",
        "",
    ).strip()

    if content:

        Comment.objects.create(
            user=request.user,
            tv_show=tv_show,
            season_number=season_number,
            episode_number=None,
            content=content,
        )

    comments = get_comments_for_tv_scope(
        tv_show=tv_show,
        season_number=season_number,
        episode_number=None,
    )

    return comment_response(
        request,
        comments,
    )


# ============================================================
# ADD TV EPISODE COMMENT
# ============================================================

@login_required
def add_tv_episode_comment(
    request,
    tv_show_id,
    season_number,
    episode_number,
):

    if request.method != "POST":
        return redirect("/")

    tv_show = get_object_or_404(
        TVShow,
        id=tv_show_id,
    )

    content = request.POST.get(
        "content",
        "",
    ).strip()

    if content:

        Comment.objects.create(
            user=request.user,
            tv_show=tv_show,
            season_number=season_number,
            episode_number=episode_number,
            content=content,
        )

    comments = get_comments_for_tv_scope(
        tv_show=tv_show,
        season_number=season_number,
        episode_number=episode_number,
    )

    return comment_response(
        request,
        comments,
    )


# ============================================================
# REPLY TO COMMENT
# ============================================================

@login_required
def reply_comment(request, comment_id):

    comment = get_object_or_404(
        Comment,
        id=comment_id,
    )

    if request.method != "POST":

        return redirect(
            request.META.get(
                "HTTP_REFERER",
                "/",
            )
        )

    content = request.POST.get(
        "content",
        "",
    ).strip()

    if content:

        Comment.objects.create(
            user=request.user,
            movie=comment.movie,
            tv_show=comment.tv_show,
            season_number=comment.season_number,
            episode_number=comment.episode_number,
            parent=comment,
            content=content,
        )

    comments = get_comments_for_comment(comment)

    return comment_response(
        request,
        comments,
    )


# ============================================================
# LIKE / UNLIKE COMMENT
# ============================================================

@login_required
def like_comment(request, comment_id):

    comment = get_object_or_404(
        Comment,
        id=comment_id,
    )

    if request.method != "POST":

        return redirect(
            request.META.get(
                "HTTP_REFERER",
                "/",
            )
        )

    if comment.likes.filter(
        id=request.user.id
    ).exists():

        comment.likes.remove(request.user)

    else:

        comment.likes.add(request.user)

    comments = get_comments_for_comment(comment)

    return comment_response(
        request,
        comments,
    )


# ============================================================
# DELETE COMMENT
# ============================================================

@login_required
def delete_comment(request, comment_id):

    comment = get_object_or_404(
        Comment,
        id=comment_id,
    )

    if comment.user != request.user:

        return HttpResponseForbidden(
            "You can only delete your own comments."
        )

    if request.method != "POST":

        return redirect(
            request.META.get(
                "HTTP_REFERER",
                "/",
            )
        )

    # Save the scope before deleting.
    movie = comment.movie
    tv_show = comment.tv_show
    season_number = comment.season_number
    episode_number = comment.episode_number

    comment.delete()

    # Refresh only the relevant comment section.
    if movie:

        comments = get_comments_for_movie(movie)

    elif tv_show:

        comments = get_comments_for_tv_scope(
            tv_show=tv_show,
            season_number=season_number,
            episode_number=episode_number,
        )

    else:

        comments = Comment.objects.none()

    return comment_response(
        request,
        comments,
    )
