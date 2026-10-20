from django.urls import path
from .views import (staff_login_view, verify_staff_otp_view, resend_staff_otp_view, staff_logout_view, 
                    verify_for_staff_change_password_view, staff_change_password_view,
                    reset_staff_password_view, use_reset_staff_password_link_view,
                    change_email_view, finish_email_change_view, revert_email_change_view,
                    new_staff_account_creation_view
                    )


urlpatterns = [
    path("auth/login", staff_login_view, name="staff_login"),
    path("auth/verify-otp", verify_staff_otp_view, name="verify_otp_staff"),
    path("auth/verify-otp/resend", resend_staff_otp_view, name="resend_staff_otp"),
    path("auth/logout", staff_logout_view, name="staff_logout"),
    path("auth/change-password/verify-staff", verify_for_staff_change_password_view, name="staff_verify_staff_change_password"),
    path("auth/change-password", staff_change_password_view, name="staff_change_password"),
    path("auth/reset-password/<str:user>", reset_staff_password_view, name="staff_reset_password"),
    path("auth/reset-password/use/<idb64>/<token>", use_reset_staff_password_link_view),
    path("change-email", change_email_view, name="staff_change_email"),
    path("change-email/<rand>/<track_idb64>/<staff_idb64>/<token>", finish_email_change_view),
    path("change-email/<rand>/<track_idb64>/<staff_idb64>/<token>/revert-change", revert_email_change_view),
    path("auth/new-staff-account-creation/<idb64>/<token>", new_staff_account_creation_view),
]