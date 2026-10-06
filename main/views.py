import json
from django.shortcuts import (render, get_object_or_404,)
from django.forms.models  import model_to_dict
from dashboard.models import (SiteModel, HeroSectionModel, ServiceModel,)
from django.http import (JsonResponse, Http404)


def HomeView(request):
    site_info_instance = SiteModel.objects.select_related("hero", "about",).prefetch_related("services",).first()
    enabled_home_sections = site_info_instance.sections.filter(is_enabled=True).order_by("order",)



    context = {
        "site_info": model_to_dict(site_info_instance),
        "enabled_sections": enabled_home_sections,
        "hero_section": site_info_instance.hero,
        "about_description": site_info_instance.about.description,
        "services": site_info_instance.services.filter(is_active=True).order_by("-id")[:3],

        "current": "home"
    }

    return render(request, "main/home.html", context)



def AboutView(request):
    site_info_instance = SiteModel.objects.select_related("about").first()
    team_members = site_info_instance.about.team.filter(is_member=True)


    context = {
        "site_info": model_to_dict(site_info_instance),
        "about": model_to_dict(site_info_instance.about),
        "team": team_members,
        "current": "about"
    }
    return render(request, "main/about.html", context)



def ServicesView(request):
    context = {
        "current": "services"
    }

    return render(request, "main/services.html", context)


def ServiceDetailView(request, service_slug):
    # site_info_instance = SiteModel.objects.select_related("about",).first()
    service = ServiceModel.objects.prefetch_related("packages", "related_services", "faqs",).filter(slug=service_slug).first()
    service_faqs = list(service.faqs.filter().order_by("-id")[:5]) # latest 5 faqs

    context = {
        "service": service,
        "packages": service.packages.filter(is_removed=False),
        "related_services": service.related_services.filter(is_active=True),
        "faqs": service_faqs[:4],
        "more_faqs": len(service_faqs) == 5,

        "current": "services"
    }

    context["faqs_batch_point"] = service_faqs[-2].id if context["more_faqs"] else None



    return render(request, "main/service_detail.html", context)



def GetFAQsBatch(request, service_slug, faqs_batch_point):
    service = ServiceModel.objects.prefetch_related("faqs").filter(slug=service_slug).first()

    if service:
        batch_faqs = list(service.faqs.filter(pk__lt=faqs_batch_point).order_by("-id")[:6])

        faqs = list()

        for faq in batch_faqs[:5]:
            item = {
                "question": faq.question,
                "answer": faq.answer
            }

            faqs.append(item)

        context = {
            "faqs": faqs,
            "more_faqs": len(batch_faqs) == 6
        }

        context["faqs_batch_point"] = batch_faqs[-2].id if context["more_faqs"] else None


        return JsonResponse(context)

    raise Http404