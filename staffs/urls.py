from django.urls import path
from .views import (StaffLoginView, VerifyStaffLoginOTP, ResendStaffOTPView, StaffLogoutView)

urlpatterns = [
    path("login", StaffLoginView, name="staff_login"),
    path("login/verify-otp", VerifyStaffLoginOTP, name="verify_otp_staff"),
    path("login/verify-otp/resend", ResendStaffOTPView, name="resend_staff_otp"),
    path("logout", StaffLogoutView, name="staff_logout")
]