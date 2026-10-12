from django.urls import path
from .views import (about_view, get_faqs_batch_view, home_view, 
    service_detail_view, services_view, 
    testimonials_view, submit_testimonial_view, get_testimonials_batch_view, 
    contact_view, submit_contact_view, contact_get_faqs_batch_view
)


urlpatterns = [
    path("", home_view, name="main_home"),
    path("about", about_view, name="main_about"),
    path("services", services_view, name="main_services"),
    path("services/<slug:service_slug>", service_detail_view, name="main_service_detail"),
    path("services/<slug:service_slug>/<int:faqs_batch_point>", get_faqs_batch_view, name="get_faqs_batch"),
    path("testimonials", testimonials_view, name="main_testimonials"),
    path("testimonials/submit-testimonial", submit_testimonial_view, name="main_submit_testimonial"),
    path("testimonials/get-testimonials-batch/<int:batch_point>", get_testimonials_batch_view, name="get_testimonials_batch"),
    path("contact", contact_view, name="main_contact"),
    path("contact/submit-contact-message", submit_contact_view, name="main_submit_contact"),
    path("contact/get-faqs-batch/<int:batch_point>", contact_get_faqs_batch_view, name="contact_get_faqs_batch")
]
