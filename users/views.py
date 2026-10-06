import secrets
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import (
    authenticate,
    get_user_model,
    login,
    logout,
)
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from comments.models import Comment
from .forms import ProfilePictureForm

User = get_user_model()

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
    
def forgot_password(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip()

        if not email:
            messages.error(request, "Please enter your email.")
            return render(request, "forgot_password.html")

        user = User.objects.filter(email__iexact=email).first()

        if not user:
            messages.error(request, "No account found with this email.")
            return render(request, "forgot_password.html")

        # Generate 6 digit OTP
        otp = str(secrets.randbelow(900000) + 100000)

        # Save reset information in session
        request.session["reset_user_id"] = user.pk
        request.session["reset_otp"] = make_password(otp)
        request.session["reset_otp_expiry"] = (
            timezone.now() + timedelta(minutes=10)
        ).timestamp()
        request.session["reset_otp_attempts"] = 0

        # Send OTP
        send_mail(
            subject="Calypso - Password Reset OTP",
            message=(
                f"Your Calypso password reset OTP is: {otp}\n\n"
                "This OTP is valid for 10 minutes.\n"
                "If you did not request this, please ignore this email."
            ),
            from_email=None,
            recipient_list=[user.email],
            fail_silently=False,
        )

        messages.success(
            request,
            "OTP has been sent to your registered email."
        )

        return redirect("/users/verify-otp/")

    return render(request, "forgot_password.html")


def verify_otp(request):
    if not request.session.get("reset_user_id"):
        return redirect("/users/forgot-password/")

    if request.method == "POST":
        entered_otp = request.POST.get("otp", "").strip()

        stored_otp = request.session.get("reset_otp")
        expiry = request.session.get("reset_otp_expiry")
        attempts = request.session.get("reset_otp_attempts", 0)

        if not stored_otp or not expiry:
            request.session.flush()
            messages.error(
                request,
                "OTP session expired. Please request a new OTP."
            )
            return redirect("/users/forgot-password/")

        # Check expiry
        if timezone.now().timestamp() > expiry:
            request.session.flush()
            messages.error(
                request,
                "OTP has expired. Please request a new OTP."
            )
            return redirect("/users/forgot-password/")

        # Maximum 5 attempts
        if attempts >= 5:
            request.session.flush()
            messages.error(
                request,
                "Too many incorrect attempts. Please request a new OTP."
            )
            return redirect("/users/forgot-password/")

        # Verify OTP
        if check_password(entered_otp, stored_otp):
            request.session["otp_verified"] = True

            messages.success(
                request,
                "OTP verified successfully."
            )

            return redirect("/users/reset-password/")

        request.session["reset_otp_attempts"] = attempts + 1

        messages.error(request, "Invalid OTP.")

    return render(request, "verify_otp.html")


def reset_password(request):
    if not request.session.get("otp_verified"):
        return redirect("/users/forgot-password/")

    user_id = request.session.get("reset_user_id")

    if not user_id:
        request.session.flush()
        return redirect("/users/forgot-password/")

    user = User.objects.filter(pk=user_id).first()

    if not user:
        request.session.flush()
        messages.error(request, "User not found.")
        return redirect("/users/forgot-password/")

    if request.method == "POST":
        password = request.POST.get("password", "")
        confirm_password = request.POST.get("confirm_password", "")

        if not password or not confirm_password:
            messages.error(
                request,
                "Please enter both password fields."
            )
            return render(request, "reset_password.html")

        if password != confirm_password:
            messages.error(
                request,
                "Passwords do not match."
            )
            return render(request, "reset_password.html")

        # Use Django's password validators
        try:
            validate_password(password, user)
        except ValidationError as error:
            for message in error.messages:
                messages.error(request, message)

            return render(request, "reset_password.html")

        # Change password
        user.set_password(password)
        user.save()

        # Clear reset session
        request.session.flush()

        messages.success(
            request,
            "Password changed successfully. Please login again."
        )

        return redirect("/users/login/")

    return render(request, "reset_password.html")