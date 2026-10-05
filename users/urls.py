from django.urls import path

from . import views


urlpatterns = [

    # ========================================================
    # AUTHENTICATION
    # ========================================================

    path(
        "register/",
        views.register_view,
        name="register",
    ),

    path(
        "login/",
        views.login_view,
        name="login",
    ),

    path(
        "logout/",
        views.logout_view,
        name="logout",
    ),


    # ========================================================
    # PROFILE
    # ========================================================

    path(
        "profile/",
        views.profile_view,
        name="profile",
    ),

    path(
        "profile/<str:username>/",
        views.user_profile_view,
        name="user-profile",
    ),


    # ========================================================
    # DASHBOARD
    # ========================================================

    path(
        "dashboard/",
        views.dashboard_view,
        name="dashboard",
    ),


    # ========================================================
    # FOLLOWING / FOLLOWERS
    # ========================================================

    path(
        "following/",
        views.following_view,
        name="following",
    ),

    path(
        "followers/",
        views.followers_view,
        name="followers",
    ),

    path(
        "follow/<str:username>/",
        views.follow_user_view,
        name="follow-user",
    ),

    path(
        "unfollow/<str:username>/",
        views.unfollow_user_view,
        name="unfollow-user",
    ),
]