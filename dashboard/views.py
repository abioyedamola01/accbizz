from django.shortcuts import (render, redirect,)
from django.urls import reverse
from django.contrib.auth.decorators import (login_required, permission_required,)
from django.forms.models import model_to_dict
from .forms import (EditProfileForm, UpdateAvatarForm, SiteInfoForm, SiteHomeSectionUpdateFormset, HeroInfoForm, HeroImgForm, AboutForm, TeamForm, FAQForm, ServiceForm,)
from .models import (SiteModel, HeroSectionModel, AboutSectionModel, TeamModel, FAQsModel, ServiceModel)
from .utils import (toast_json_ok, toast_json_error,)



# Create your views here.
@login_required()
@permission_required("staffs.view_dashboard", raise_exception=True)
def dashboard_home_view(request):
    
    context = {}

    return render(request, "dashboard/home.html", context)




@login_required
@permission_required("staffs.view_dashboard", raise_exception=True)
def profile_view(request):
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
def update_profile_avatar_view(request):
    avatar_form = UpdateAvatarForm(request.POST or None, request.FILES or None)

    if request.POST and avatar_form.is_valid():
        avatar_form = UpdateAvatarForm(request.POST, request.FILES, instance=request.user.profile)
        avatar_form.save()

        return toast_json_ok("Profile picture updated successfully.")
    return toast_json_error("Can't update profile picture.")


@login_required
@permission_required("staffs.view_dashboard", raise_exception=True)
def update_profile_info_view(request):
    profile_edit_form = EditProfileForm(request.POST or None)

    if request.POST and profile_edit_form.is_valid():
        profile_edit_form = EditProfileForm(request.POST, instance=request.user.profile)
        profile_edit_form.save()

        return toast_json_ok("Profile updated successfully.")
    return toast_json_error("Can't update profile.")







@login_required
@permission_required(("staffs.view_dashboard", "staffs.manage_site", "staffs.manage_homepage",), raise_exception=True)
def site_view(request):
    site_info_instance = SiteModel.objects.first()
    site_info_form = SiteInfoForm(request.POST or None, instance=site_info_instance)    

    context = {
        "current": "site",
        "site_form": site_info_form,
        "site_info": model_to_dict(site_info_instance),
        "site_info_last_updated": site_info_instance.last_updated,
    }
    return render(request, "dashboard/site.html", context)




@login_required
@permission_required(("staffs.view_dashboard", "staffs.manage_site", ), raise_exception=True)
def update_site_info_view(request):
    site_info = SiteModel.objects.first()
    site_info_form = SiteInfoForm(request.POST or None, instance=site_info)
    if request.POST and site_info_form.is_valid():
        site_info_form.save()

        return toast_json_ok("Site info updated successfully.")
    return toast_json_error("Can't update site info.")



@login_required
@permission_required(("staffs.view_dashboard", "staffs.manage_site", "staffs.manage_homepage",), raise_exception=True)
def update_site_home_sections_view(request):
    section_formset = SiteHomeSectionUpdateFormset(request.POST or None)
    if request.POST and section_formset.is_valid():
        section_formset.save()

        return toast_json_ok("Home sections updated successfully.")
    return toast_json_error("Can't update home sections.")






@login_required
@permission_required(("staffs.manage_contents"), raise_exception=True)
def contents_view(request):
    tab = str(request.GET.get("tab")).lower()
    tab = tab if tab in ["home", "about", "services", "faqs", "contacts"] else "home"

    context = {}

    if tab == "home":
        site_info_instance = SiteModel.objects.first()
        home_sections = site_info_instance.sections.order_by("order",)
        section_formset = SiteHomeSectionUpdateFormset(request.POST or None, queryset=home_sections)
        

        hero_instance = HeroSectionModel.objects.first()
        hero_form = HeroInfoForm(request.POST or None, instance=hero_instance)
        hero_img_form = HeroImgForm(request.POST or None, instance=hero_instance)

        context = {
            "section_formset": section_formset,
            "hero_form": hero_form,
            "hero_img_form": hero_img_form
        }
    elif tab == "about":
        about_instance = AboutSectionModel.objects.first()
        about_form = AboutForm(request.POST or None, instance=about_instance)
        team_members = about_instance.team.order_by("-id",).filter(is_member=True)
        team_form = TeamForm()

        context = {
            "about_form": about_form,
            "team": team_members,
            "team_form":  team_form,
        }
    elif tab== "services":
        services = ServiceModel.objects.filter().order_by("-id")
        service_form = ServiceForm()
        context = {
            "services": services,
            "service_form": service_form
        }

    elif tab == "faqs":
        faqs = FAQsModel.objects.select_related("service").filter().order_by("-id")
        services = list(ServiceModel.objects.filter().values("id", "title"))

        faq_form = FAQForm()

        context = {
            "faqs": faqs,
            "services": services,
            "faq_form": faq_form
        }


    context["content_tab"] = tab
    context["current"] = "contents"
    context["page_blurb"] = "Manage all the contents displayed across your website."

    return render(request, "dashboard/contents.html", context)



@login_required
@permission_required(("staffs.manage_contents", "staffs.manage_hero",), raise_exception=True)
def update_hero_view(request, type):
    hero_instance = HeroSectionModel.objects.first()
    hero_form = HeroInfoForm(request.POST or None, instance=hero_instance) if type == "info" else HeroImgForm(request.POST or None, request.FILES or None, instance=hero_instance)

    if type == "reset":
        hero_instance.img = ""
        hero_instance.save(update_fields=("img",))

        return redirect("dashboard_contents")
    elif hero_form and request.POST and hero_form.is_valid():
        hero_form.save()

        return toast_json_ok("Hero updated successfully.")
    return toast_json_error("Can't update hero.")



@login_required
@permission_required(("staffs.manage_contents",), raise_exception=True)
def update_about_view(request):
    about_instance = AboutSectionModel.objects.first()
    about_form = AboutForm(request.POST or None, instance=about_instance)

    if request.POST and about_form.is_valid:
        about_form.save()

        return toast_json_ok(f"About info has been updated successfully.")
            
    return toast_json_error(f"Can't update about info.")


@login_required
@permission_required(("staffs.manage_contents", "staffs.manage_team", "staffs.update_team_member"), raise_exception=True)
def update_team_member_view(request, member):
    team_member = TeamModel.objects.filter(slug=member).first()
    team_form = TeamForm(request.POST or None, request.FILES or None, instance=team_member)

    if  request.POST and team_form.is_valid():
        team_form.save()
        return toast_json_ok(f"{team_member.name} has been updated successfully.")
            
    return toast_json_error(f"Can't update {team_member.name}")
    

@login_required
@permission_required(("staffs.manage_contents", "staffs.manage_team", "staffs.remove_team_member"), raise_exception=True)
def remove_team_member_view(request, member):
    team_member = TeamModel.objects.filter(slug=member).first()

    if team_member:
        team_member.remove_as_member()
        return toast_json_ok(f"{team_member.name} has been removed successfully.")
                
    return toast_json_error(f"Can't remove {team_member.name}")



@login_required
@permission_required(("staffs.manage_contents", "staffs.manage_team", "staffs.add_team_member"), raise_exception=True)
def add_team_member_view(request):
    team_form = TeamForm(request.POST or None, request.FILES or None)

    if request.POST and team_form.is_valid():
        team_form.save()
        return toast_json_ok(f"Team member has been added successfully.")
            
    return toast_json_error(f"Can't add team member.")




@login_required
@permission_required(("staffs.manage_contents", "staffs.manage_services", "staffs.update_service"), raise_exception=True)
def update_service_view(request, service):
    service_inst = ServiceModel.objects.filter(slug=service).first()
    service_form = ServiceForm(request.POST or None, instance=service_inst)

    if request.POST and service_form.is_valid():
        print(service_inst)
        service_form.save()

        return toast_json_ok(f"{service_inst.title} was updated successfully.")
    return toast_json_error(f"can't update {service_inst.title}")




@login_required
@permission_required(("staffs.manage_contents", "staffs.manage_services", "staffs.delete_service"), raise_exception=True)
def delete_service_view(request, service):
    service_inst = ServiceModel.objects.filter(slug=service).first()

    if service_inst:
        service_inst.delete()

        return toast_json_ok(f"{service_inst.title} has been deleted successfully.")
    return toast_json_error("Can't delete service.")



@login_required
@permission_required(("staffs.manage_contents", "staffs.manage_services", "staffs.add_service"), raise_exception=True)
def add_service_view(request):
    service_form = ServiceForm(request.POST or None)

    if request.POST or service_form.is_valid():
        service_form.save()

        return toast_json_ok("Service added successfully.")
    return toast_json_error("Can't add service")




@login_required
@permission_required(("staffs.manage_contents", "staffs.manage_faqs", "staffs.update_faq"), raise_exception=True)
def update_faq_view(request, faq):
    faq_inst = FAQsModel.objects.filter(slug=faq).first()
    faqs_form = FAQForm(request.POST or None, instance=faq_inst)

    if request.POST and faqs_form.is_valid() and faq_inst:
        faqs_form.save()

        return toast_json_ok(f"{faq_inst.question} has been updated successfully.")
    
    return toast_json_error(f"Can't update {faq_inst.question}")
    


@login_required
@permission_required(("staffs.manage_contents", "staffs.manage_faqs", "staffs.delete_faq"), raise_exception=True)
def delete_faq_view(request, faq):
    faq_inst = FAQsModel.objects.filter(slug=faq).first()

    if faq_inst:
        faq_inst.delete()
        return toast_json_ok(f"{faq_inst.question} has been deleted successfully.")
            
    return toast_json_error(f"Can't delete {faq_inst.question}")


@login_required
@permission_required(("staffs.manage_contents", "staffs.manage_faqs", "staffs.add_faq"), raise_exception=True)
def add_faq_view(request):
    faq = FAQForm(request.POST or None)

    if (request.POST and faq.is_valid() and faq):
        faq.save()
        return toast_json_ok("FAQ added successfully.")

    return toast_json_error("Can't add FAQ.")
