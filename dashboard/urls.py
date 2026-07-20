from django.urls import path
from .views import (DashboardHomeView, ProfileView, UpdateProfileAvatarView,UpdateProfileInfoView, SiteView, UpdateSiteInfoView, UpdateSiteHomeSectionsView,)


urlpatterns = [
    path("", DashboardHomeView, name="dashboard_home"),
    path("profile", ProfileView, name="dashboard_profile"),
    path("profile/update-profile-avatar", UpdateProfileAvatarView, name="update_profile_avatar"),
    path("pofile/update-profile-info", UpdateProfileInfoView, name="update_profile_info"),
    path("site", SiteView, name="dashboard_site"),
    path("site/update-site-info", UpdateSiteInfoView, name="dashboard_update_site_info"),
    path("site/update-site-home-sections", UpdateSiteHomeSectionsView, name="dashboard_update_home_sections"),
]
