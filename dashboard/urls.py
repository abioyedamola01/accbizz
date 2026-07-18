from django.urls import path
from .views import (
    DashboardHomeView,
    ProfileView,
    UpdateProfileAvatarView,
    UpdateProfileInfoView,
)


urlpatterns = [
    path("", DashboardHomeView, name="dashboard_home"),
    path("profile", ProfileView, name="dashboard_profile"),
    path("profile/update_profile_avatar", UpdateProfileAvatarView, name="update_profile_avatar"),
    path("pofile/update_profile_info", UpdateProfileInfoView, name="update_profile_info")
]
