from django.shortcuts import (render, redirect,)
from django.contrib.auth.decorators import (login_required, permission_required,)
from django.forms.models import model_to_dict
from .forms import (EditProfileForm, UpdateAvatarForm, SiteInfoForm, SiteHomeSectionUpdateFormset, HeroInfoForm, HeroImgForm)
from .models import (SiteModel, HeroSectionModel,)


# Create your views here.
@login_required()
@permission_required("staffs.view_dashboard", raise_exception=True)
def DashboardHomeView(request):
    return render(request, "dashboard/home.html", {})




@login_required
@permission_required("staffs.view_dashboard", raise_exception=True)
def ProfileView(request):
    profile_form = EditProfileForm(request.POST or None, instance=request.user.profile)
    avatar_form = UpdateAvatarForm()
    profile = request.user.profile
    profile_info = list()
    for field, value in model_to_dict(profile).items():
        if field not in ("id", "avatar", "last_updated"):
            field_name = str(field).replace("_", " ").title()
            if field == "role":
                value = profile.get_role_display()
            if field == "gender":
                value = profile.get_gender_display()

            profile_info.append((field_name, value))
    

    context = {
        "current": "staff profile",
        "profile_info": profile_info,
        "profile_form": profile_form,
        "avatar_form":  avatar_form
    }
    return render(request, "dashboard/profile.html", context)




@login_required
@permission_required("staffs.view_dashboard", raise_exception=True)
def UpdateProfileAvatarView(request):
    avatar_form = UpdateAvatarForm(request.POST or None, request.FILES or None)

    if request.POST and avatar_form.is_valid():
        avatar_form = UpdateAvatarForm(request.POST, request.FILES, instance=request.user.profile)
        avatar_form.save()

    return redirect("dashboard_profile")


@login_required
@permission_required("staffs.view_dashboard", raise_exception=True)
def UpdateProfileInfoView(request):
    profile_edit_form = EditProfileForm(request.POST or None)

    if request.POST and profile_edit_form.is_valid():
        profile_edit_form = EditProfileForm(request.POST, instance=request.user.profile)
        profile_edit_form.save()

    return redirect("dashboard_profile")







@login_required
@permission_required(("staffs.view_dashboard", "staffs.manage_site", "staffs.manage_homepage",), raise_exception=True)
def SiteView(request):
    site_info_instance = SiteModel.objects.first()
    site_info_form = SiteInfoForm(request.POST or None, instance=site_info_instance)
    home_sections = site_info_instance.sections.order_by("order",)
    section_formset = SiteHomeSectionUpdateFormset(request.POST or None, queryset=home_sections)


    context = {
        "current": "site",
        "site_form": site_info_form,
        "site_info": model_to_dict(site_info_instance),
        "site_info_last_updated": site_info_instance.last_updated,

        
        "section_formset": section_formset,
    }
    return render(request, "dashboard/site.html", context)




@login_required
@permission_required(("staffs.view_dashboard", "staffs.manage_site", ), raise_exception=True)
def UpdateSiteInfoView(request):
    site_info = SiteModel.objects.first()
    site_info_form = SiteInfoForm(request.POST or None, instance=site_info)
    if request.POST and site_info_form.is_valid():
        site_info_form.save()

    return redirect("dashboard_site")



@login_required
@permission_required(("staffs.view_dashboard", "staffs.manage_site", "staffs.manage_homepage",), raise_exception=True)
def UpdateSiteHomeSectionsView(request):
    section_formset = SiteHomeSectionUpdateFormset(request.POST or None)
    if request.POST and section_formset.is_valid():
        section_formset.save()
        

    return redirect("dashboard_site")






@login_required
@permission_required(("staffs.manage_site", "staffs.manage_contents"), raise_exception=True)
def ContentsView(request):
    hero_instance = HeroSectionModel.objects.first()
    hero_form = HeroInfoForm(request.POST or None, instance=hero_instance)
    hero_img_form = HeroImgForm(request.POST or None, instance=hero_instance)
    context = {
        "hero_form": hero_form,
        "hero_img_form": hero_img_form,

        "current": "contents",
        "page_blurb": "Manage all the contents displayed across your website."
    }

    return render(request, "dashboard/contents.html", context)



@login_required
@permission_required(("staffs.manage_site", "staffs.manage_contents", "staffs.manage_hero",), raise_exception=True)
def UpdateHeroView(request, type):
    hero_instance = HeroSectionModel.objects.first()
    hero_form = HeroInfoForm(request.POST or None, instance=hero_instance) if type == "info" else HeroImgForm(request.POST or None, request.FILES or None, instance=hero_instance)

    if type == "reset":
        hero_instance.img = ""
        hero_instance.save(update_fields=("img",))
    elif hero_form and request.POST and hero_form.is_valid():
        hero_form.save()

    return redirect("dashboard_contents")
