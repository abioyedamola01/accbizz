from django.http import (Http404, JsonResponse,)
from django.shortcuts import (render, get_object_or_404,)
from django.forms.models  import model_to_dict
from dashboard.models import (SiteModel, HeroSectionModel, ServiceModel, TestimonialModel)
from dashboard.forms import TestimonialForm
from dashboard.utils import (toast_json_ok, toast_json_error,)


def home_view(request):
    site_info_instance = SiteModel.objects.select_related("hero", "about",).prefetch_related("services",).first()
    enabled_home_sections = site_info_instance.sections.filter(is_enabled=True).order_by("order",)



    context = {
        "site_info": model_to_dict(site_info_instance),
        "enabled_sections": enabled_home_sections,
        "hero_section": site_info_instance.hero,
        "about_description": site_info_instance.about.description,
        "services": site_info_instance.services.filter(is_active=True).order_by("?")[:3],

        "current": "home"
    }

    return render(request, "main/home.html", context)



def about_view(request):
    site_info_instance = SiteModel.objects.select_related("about").first()
    team_members = site_info_instance.about.team.filter(is_member=True)


    context = {
        "site_info": model_to_dict(site_info_instance),
        "about": model_to_dict(site_info_instance.about),
        "team": team_members,
        "current": "about"
    }
    return render(request, "main/about.html", context)



def services_view(request):
    services = ServiceModel.objects.filter(is_active=True).order_by("?")

    context = {
        "current": "services",
        "services": services
    }

    return render(request, "main/services.html", context)


def service_detail_view(request, service_slug):
    # site_info_instance = SiteModel.objects.select_related("about",).first()
    service = ServiceModel.objects.prefetch_related("related_services", "faqs", "testimonials",).filter(slug=service_slug).first()
    testimonials = service.testimonials.filter()
    if not service:
        raise Http404()
    
    service_faqs = list(service.faqs.filter().order_by("-id")[:5]) # latest 5 faqs

    context = {
        "service": service,
        "related_services": service.related_services.filter(is_active=True),
        "faqs": service_faqs[:4],
        "more_faqs": len(service_faqs) == 5,
        "testimonials": testimonials,
        "current": "services"
    }

    context["faqs_batch_point"] = service_faqs[-2].id if context["more_faqs"] else None



    return render(request, "main/service_detail.html", context)



def get_faqs_batch_view(request, service_slug, faqs_batch_point):
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



def testimonials_view(request):
    testimonials = list(TestimonialModel.objects.filter(is_approved=True).order_by("-id")[:7])
    testimonial_form = TestimonialForm()
    context = {
        "testimonials": testimonials[:6],
        "testimonial_form": testimonial_form,
        "current": "testimonials"
    }

    batch_point = testimonials[5].id if len(testimonials) == 7 else None
    context["batch_point"] = batch_point
    print(batch_point)
    return render(request, "main/testimonials.html", context)




def get_testimonials_batch_view(request, batch_point):
    testimonials = list(TestimonialModel.objects.filter(is_approved=True, id__lt=batch_point).order_by("-id")[:7])

    items = list()

    for t in testimonials[:6]:
        service = t.service.title if t.service else None

        item = {
            "name": t.name,
            "title": t.title,
            "quote": t.quote,
            "service": service
        }

        items.append(item)

    
    context = {
        "testimonials": items
    }

    context["more_testimonials"] = True if len(testimonials) == 7 else False
    context["batch_point"] = testimonials[5].id if len(testimonials) == 7 else None

    print(context)

    return JsonResponse(context)



def submit_testimonial_view(request):
    testimonials_form = TestimonialForm(request.POST or None)

    if request.POST and testimonials_form.is_valid:
        testimonials_form.save()

        return toast_json_ok("Testimonial submitted successfully.")
    return toast_json_error("Can't submit testimonial.")