from django.urls import path
from .views import (staff_login_view, verify_staff_login_otp_view, resend_staff_otp_view, staff_logout_view)


urlpatterns = [
    path("login", staff_login_view, name="staff_login"),
    path("login/verify-otp", verify_staff_login_otp_view, name="verify_otp_staff"),
    path("login/verify-otp/resend", resend_staff_otp_view, name="resend_staff_otp"),
    path("logout", staff_logout_view, name="staff_logout")
]