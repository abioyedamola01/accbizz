from django.urls import path
from .views import (HomeView, AboutView,)


urlpatterns = [
    path("", HomeView, name="main_home"),
    path("about", AboutView, name="main_about"),
]
