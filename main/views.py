from django.http import (Http404, JsonResponse,)
from django.shortcuts import (render, get_object_or_404,)
from django.forms.models  import model_to_dict
from dashboard.models import (SiteModel, HeroSectionModel, ServiceModel, TestimonialModel, FAQsModel,)
from dashboard.forms import (TestimonialForm, ContactMessageForm,)
from dashboard.utils import (toast_json_ok, toast_json_error, get_items_batch,)
from django.template.loader import render_to_string
from .utils import send_contact_message



def home_view(request):
    site_info_instance = SiteModel.objects.select_related("hero", "about",).prefetch_related("services",).first()
    enabled_home_sections = site_info_instance.sections.filter(is_enabled=True).order_by("order",)
    testimonials = TestimonialModel.objects.filter(is_approved=True).order_by("?")[:10]

    context = {
        "enabled_sections": enabled_home_sections,
        "hero_section": site_info_instance.hero,
        "about": site_info_instance.about,
        "services": site_info_instance.services.filter(is_active=True, is_featured=True).order_by("?")[:3],
        "testimonials": testimonials,
        "current": "home"
    }

    return render(request, "main/home.html", context)


def refresh_testimonials_view(request):
    testimonials = TestimonialModel.objects.filter(is_approved=True).order_by("?")[:10]

    items = list()

    for testimonial in testimonials:
        item = model_to_dict(testimonial, fields=("name", "title", "quote",))
        item["service"] = testimonial.service.title if testimonial.service else None
        items.append(item)

    context = {
        "testimonials": items
    }

    return JsonResponse(context, status=200)
    



def about_view(request):
    site_info_instance = SiteModel.objects.select_related("about").first()
    team_members = site_info_instance.about.team.filter(is_member=True)

    intro_texts = [
        "We turn struggling grades into lasting confidence",
        "Academic support that meets you where you are",
        "Stuck on your project? We help you move forward",
        "Support that makes hard topics click"
    ]

    context = {
        "about": model_to_dict(site_info_instance.about),
        "team": team_members,
        # "intro": intro_texts,
        "current": "about"
    }

    print(model_to_dict(site_info_instance.about)["intro"])
    return render(request, "main/about.html", context)



def services_view(request):
    services = ServiceModel.objects.filter(is_active=True).order_by("-id").values("title", "slug", "blurb")

    context = {
        "current": "services",
        "services": services
    }

    return render(request, "main/services.html", context)


def service_detail_view(request, service_slug):
    service = ServiceModel.objects.prefetch_related("related_services", "faqs", "testimonials",).filter(slug=service_slug).first()
    faqs = list(service.faqs.filter().order_by("-id")[:6])
    more_faqs = len(faqs) == 6

    if not service:
        raise Http404()

    testimonials = service.testimonials.filter(is_approved=True)
    

    context = {
        "service": service,
        "related_services": service.related_services.filter(is_active=True),
        "faqs": faqs[:5],
        "more_faqs": more_faqs,
        "faqs_batch_point": faqs[-1].id if more_faqs else None,
        "testimonials": testimonials,
        "current": "services"
    }


    return render(request, "main/service_detail.html", context)


def get_faqs_batch_view(request, service_slug, faqs_batch_point):
    service = ServiceModel.objects.prefetch_related("faqs").filter(slug=service_slug).first()
    faqs = list(service.faqs.filter(pk__lte=faqs_batch_point).order_by("-id")[:7])
    more_faqs = len(faqs) == 7

    context = {}

    if service and faqs:
        html = render_to_string("main/partials/faqs/_faq_items.html", {"faqs": faqs[:6]})
        context = {
            "html": html,
            "more_faqs": more_faqs,
            "faqs_batch_point": faqs[-1].id if more_faqs else None
        }
    return JsonResponse(context)




def testimonials_view(request):
    testimonials = list(TestimonialModel.objects.select_related("service").filter(is_approved=True).order_by("-id")[:7])
    testimonial_form = TestimonialForm()
    context = {
        "testimonials": testimonials[:6],
        "testimonial_form": testimonial_form,
        "current": "testimonials"
    }

    batch_point = testimonials[-1].id if len(testimonials) == 7 else None
    context["batch_point"] = batch_point
    return render(request, "main/testimonials.html", context)



def get_testimonials_batch_view(request, batch_point):
    context = get_items_batch(
        query=TestimonialModel.objects.filter(is_approved=True, id__lt=batch_point).order_by("-id"),
        size=6,
        tmp="main/partials/testimonials/_cards.html",
        name="testimonials",
        point_field="id"
    )
    return JsonResponse(context)
   



def submit_testimonial_view(request):
    testimonials_form = TestimonialForm(request.POST or None)

    if request.POST and testimonials_form.is_valid:
        testimonials_form.save()

        return toast_json_ok("Testimonial submitted successfully.")
    return toast_json_error("Can't submit testimonial.", form_errors=testimonials_form.errors.as_json())





def contact_view(request):
    contact_form = ContactMessageForm()
   
    faqs = list(FAQsModel.objects.filter().order_by("-id")[:7])
    more_faqs = len(faqs) == 7

    context = {
        "contact_form": contact_form,
        "faqs": faqs[:6],
        "more_faqs": more_faqs,
        "faqs_batch_point": faqs[-1].id if more_faqs else None,
        "current": "contact"
    }
    
    return render(request, "main/contact.html", context)


def submit_contact_view(request):
    contact_form = ContactMessageForm(request.POST or None)

    if request.POST and contact_form.is_valid():
        data = contact_form.cleaned_data
        site_info = SiteModel.objects.filter().first()
        # send_contact_message(site_info=site_info, name=data["name"], email=data["email"],message=data["message"], phone=data["phone"], service=data["service"])
        try:
            send_contact_message(**data, site_info=site_info)
            send_status = {"status": "sent", "errror": None}
        except Exception as e:
            send_status = {"status": "failed", "errror": e}
        contact_form.save()

        return toast_json_ok("Message sent successfully.", send_status=send_status)
    return toast_json_error("Can't send message", form_errors=contact_form.errors.as_json())



def contact_get_faqs_batch_view(request, batch_point):
    context = get_items_batch(
        query=FAQsModel.objects.filter(id__lte=batch_point).order_by("-id"),
        size=7,
        tmp="main/partials/faqs/_faq_items.html",
        name="faqs",
        point_field="id"
    )

    return JsonResponse(context)