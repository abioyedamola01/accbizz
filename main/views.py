from django.shortcuts import render
from django.forms.models  import model_to_dict
from dashboard.models import (SiteModel, HeroSectionModel,)


def HomeView(request):
    site_info_instance = SiteModel.objects.select_related("hero", "about",).first()
    

    enabled_home_sections = list(site_info_instance.sections.filter(is_enabled=True).order_by("order",))

    context = {
        "site_info": model_to_dict(site_info_instance),
        "enabled_sections": enabled_home_sections,
        "hero_section": site_info_instance.hero,
        "about_description": site_info_instance.about.description,


        "current": "home"
    }

    return render(request, "main/home.html", context)



def AboutView(request):
    site_info_instance = SiteModel.objects.select_related("about").first()
    team_members = list(site_info_instance.about.team.filter(is_member=True))


    context = {
        "site_info": model_to_dict(site_info_instance),
        "about": model_to_dict(site_info_instance.about),
        "team": team_members,
        "current": "about"
    }
    return render(request, "main/about.html", context)
