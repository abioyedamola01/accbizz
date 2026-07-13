from django.urls import path
from .views import (
    StaffLoginView,
    VerifyStaffLoginOTP,
    ResendStaffOTPView
)

urlpatterns = [
    path("login", StaffLoginView, name="staff_login"),
    path("login/verify_otp", VerifyStaffLoginOTP, name="verify_otp_staff"),
    path("login/verify_otp/resend", ResendStaffOTPView, name="resend_staff_otp")
]
