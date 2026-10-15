from django.urls import path
from .views import (staff_login_view, verify_staff_otp_view, resend_staff_otp_view, staff_logout_view, 
                    verify_for_staff_change_password_view, staff_change_password_view)


urlpatterns = [
    path("auth/login", staff_login_view, name="staff_login"),
    path("auth/verify-otp", verify_staff_otp_view, name="verify_otp_staff"),
    path("auth/verify-otp/resend", resend_staff_otp_view, name="resend_staff_otp"),
    path("auth/logout", staff_logout_view, name="staff_logout"),
    path("auth/change-password/verify-staff", verify_for_staff_change_password_view, name="staff_verify_staff_change_password"),
    path("auth/change-password", staff_change_password_view, name="staff_change_password"),
]