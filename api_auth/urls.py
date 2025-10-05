
from django.urls import re_path

from . import views

app_name = "api_auth"

# 're_path' is applied, because into 'frontend' paths do not have trailing slash,
# which is problem for a 'POST' request.
urlpatterns = [
    re_path(r"^sign-(?:in|up)/?$", views.user_register_or_login_view, name="sign-inup"),
    re_path(r"^sign-out/?$", views.user_logout_view, name="sign-out"),
    re_path(r"^profile/?$", views.user_profile_view, name="profile"),
    re_path(r"^profile/password/?$", views.change_user_password_view, name="password"),
    re_path(r"^profile/avatar/?$", views.upload_user_avatar_view, name="avatar"),
]

