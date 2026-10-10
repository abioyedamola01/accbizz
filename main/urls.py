from django.urls import path
from .views import (about_view, get_faqs_batch, home_view, service_detail_view, services_view, testimonials_view,)


urlpatterns = [
    path("", home_view, name="main_home"),
    path("about", about_view, name="main_about"),
    path("services", services_view, name="main_services"),
    path("services/<slug:service_slug>", service_detail_view, name="main_service_detail"),
    path("services/<slug:service_slug>/<int:faqs_batch_point>", get_faqs_batch, name="get_faqs_batch"),
    path("testimonials", testimonials_view, name="main_testimonials"),
]
