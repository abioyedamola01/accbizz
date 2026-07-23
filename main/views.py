from django.shortcuts import render
from django.forms.models  import model_to_dict
from dashboard.models import (SiteModel, HeroSectionModel,)


def HomeView(request):
    site_info_instance = SiteModel.objects.select_related("hero").first()

    enabled_home_sections = list(site_info_instance.sections.filter(is_enabled=True))

    context = {
        "site_info": model_to_dict(site_info_instance),
        "enabled_sections": enabled_home_sections,
        "hero_section": site_info_instance.hero,


        "current": "home"
    }

    return render(request, "main/home.html", context)
