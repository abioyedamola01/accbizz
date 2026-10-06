from django.urls import path
from .views import (HomeView, AboutView, ServicesView, ServiceDetailView, GetFAQsBatch)


urlpatterns = [
    path("", HomeView, name="main_home"),
    path("about", AboutView, name="main_about"),
    path("services", ServicesView, name="main_services"),
    path("services/<slug:service_slug>", ServiceDetailView, name="main_service_detail"),
    path("services/<slug:service_slug>/<int:faqs_batch_point>", GetFAQsBatch, name="get_faqs_batch"),
]
