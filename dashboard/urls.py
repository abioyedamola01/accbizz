from django.urls import path
from .views import (DashboardHomeView, 
                    ProfileView, UpdateProfileAvatarView, UpdateProfileInfoView, 
                    SiteView, UpdateSiteInfoView, UpdateSiteHomeSectionsView, 
                    ContentsView, UpdateHeroView, UpdateAboutView, UpdateTeamMemberView, RemoveTeamMemberView, AddTeamMemberView,)


urlpatterns = [
    path("", DashboardHomeView, name="dashboard_home"),
    path("profile", ProfileView, name="dashboard_profile"),
    path("profile/update-profile-avatar", UpdateProfileAvatarView, name="update_profile_avatar"),
    path("pofile/update-profile-info", UpdateProfileInfoView, name="update_profile_info"),
    path("site", SiteView, name="dashboard_site"),
    path("site/update-site-info", UpdateSiteInfoView, name="dashboard_update_site_info"),
    path("site/update-site-home-sections", UpdateSiteHomeSectionsView, name="dashboard_update_home_sections"),
    path("contents", ContentsView, name="dashboard_contents"),
    path("contents/home/update-hero/<slug:type>", UpdateHeroView, name="dashboard_update_hero"),
    path("contents/about/update-about-info", UpdateAboutView, name="dashboard_update_about"),
    path("contents/team/update-team-member/<slug:member>", UpdateTeamMemberView, name="dashboard_update_team_member"),
    path("contents/team/remove-team-member/<slug:member>", RemoveTeamMemberView, name="dashboard_remove_team_member"),
    path("contents/team/add-team-member", AddTeamMemberView, name="dashboard_add_team_member"),
]
