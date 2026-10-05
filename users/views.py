from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from comments.models import Comment

from .forms import ProfilePictureForm
from .models import User


# ============================================================
# REGISTER
# ============================================================

def register_view(request):

    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":

        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect("register")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect("register")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email is already registered.")
            return redirect("register")

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )

        login(request, user)

        messages.success(
            request,
            "Account created successfully."
        )

        return redirect("home")

    return render(
        request,
        "users/register.html"
    )


# ============================================================
# LOGIN
# ============================================================

def login_view(request):

    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            login(request, user)

            messages.success(
                request,
                f"Welcome back, {user.username}!"
            )

            return redirect("home")

        messages.error(
            request,
            "Invalid username or password."
        )

    return render(
        request,
        "users/login.html"
    )


# ============================================================
# LOGOUT
# ============================================================

def logout_view(request):

    logout(request)

    messages.success(
        request,
        "You have been logged out."
    )

    return redirect("home")


# ============================================================
# OWN PROFILE
# ============================================================

@login_required
def profile_view(request):

    if request.method == "POST":

        form = ProfilePictureForm(
            request.POST,
            request.FILES,
            instance=request.user
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Profile picture updated successfully."
            )

            return redirect("profile")

    else:

        form = ProfilePictureForm(
            instance=request.user
        )

    user = request.user

    follower_count = user.followers.count()
    following_count = user.following.count()
    comment_count = user.comments.count()

    return render(
        request,
        "users/profile.html",
        {
            "form": form,
            "profile_user": user,
            "follower_count": follower_count,
            "following_count": following_count,
            "comment_count": comment_count,
        }
    )


# ============================================================
# PUBLIC USER PROFILE
# ============================================================

@login_required
def user_profile_view(request, username):

    profile_user = get_object_or_404(
        User,
        username=username
    )

    is_following = request.user.following.filter(
        id=profile_user.id
    ).exists()

    follower_count = profile_user.followers.count()
    following_count = profile_user.following.count()
    comment_count = profile_user.comments.count()

    return render(
        request,
        "users/user_profile.html",
        {
            "profile_user": profile_user,
            "is_following": is_following,
            "follower_count": follower_count,
            "following_count": following_count,
            "comment_count": comment_count,
        }
    )


# ============================================================
# FOLLOW / UNFOLLOW
# ============================================================

@login_required
def follow_user_view(request, username):

    if request.method != "POST":
        return redirect("user-profile", username=username)

    profile_user = get_object_or_404(
        User,
        username=username
    )

    # Prevent following yourself
    if profile_user == request.user:

        messages.error(
            request,
            "You cannot follow yourself."
        )

        return redirect(
            "user-profile",
            username=username
        )

    # Follow
    request.user.following.add(profile_user)

    messages.success(
        request,
        f"You are now following {profile_user.username}."
    )

    return redirect(
        "user-profile",
        username=username
    )


@login_required
def unfollow_user_view(request, username):

    if request.method != "POST":
        return redirect("user-profile", username=username)

    profile_user = get_object_or_404(
        User,
        username=username
    )

    request.user.following.remove(profile_user)

    messages.success(
        request,
        f"You unfollowed {profile_user.username}."
    )

    return redirect(
        "user-profile",
        username=username
    )


# ============================================================
# FOLLOWING PAGE
# ============================================================

@login_required
def following_view(request):

    following_users = (
        request.user.following
        .all()
        .order_by("username")
    )

    return render(
        request,
        "users/following.html",
        {
            "following_users": following_users,
        }
    )


# ============================================================
# FOLLOWERS PAGE
# ============================================================

@login_required
def followers_view(request):

    follower_users = (
        request.user.followers
        .all()
        .order_by("username")
    )

    return render(
        request,
        "users/followers.html",
        {
            "follower_users": follower_users,
        }
    )


# ============================================================
# DASHBOARD
# ============================================================

@login_required
def dashboard_view(request):

    user = request.user

    comment_count = Comment.objects.filter(
        user=user
    ).count()

    follower_count = user.followers.count()
    following_count = user.following.count()

    return render(
        request,
        "users/dashboard.html",
        {
            "comment_count": comment_count,
            "follower_count": follower_count,
            "following_count": following_count,
        }
    )

@login_required
def user_profile_view(request, username):

    profile_user = get_object_or_404(
        User,
        username=username
    )

    comment_count = Comment.objects.filter(
        user=profile_user
    ).count()

    follower_count = profile_user.followers.count()

    following_count = profile_user.following.count()

    is_following = False

    if request.user != profile_user:
        is_following = profile_user.followers.filter(
            id=request.user.id
        ).exists()

    return render(
        request,
        "users/user_profile.html",
        {
            "profile_user": profile_user,
            "comment_count": comment_count,
            "follower_count": follower_count,
            "following_count": following_count,
            "is_following": is_following,
        },
    )