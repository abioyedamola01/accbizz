import random
from django.contrib.auth.hashers import (make_password, check_password)
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.crypto import get_random_string
from django.utils import timezone
from django.contrib.sessions.models import Session
from .models import (OTPVerifyModel, UserSession,)



def delete_staff_sessions(staff):
    current_sessions_keys = UserSession.objects.filter(user=staff, session__expire_date__gt=timezone.now()).values_list("session__session_key", flat=True)
    Session.objects.filter(session_key__in=current_sessions_keys).delete()


def delete_staff_other_sessions(request, staff):
    other_sessions_keys = UserSession.objects.filter(user=staff, session__expire_date__gt=timezone.now()).exclude(session__session_key=request.session.session_key).values_list("session__session_key", flat=True)
    Session.objects.filter(session_key__in=other_sessions_keys).delete()




class ChangeEmailTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, inst, timestamp):
        value = f"{inst.pk}{timestamp}{inst.last_updated}"
        return value

change_email_token_generator = ChangeEmailTokenGenerator()



def generate_otp(length=6):
    code = "".join(str(random.randint(0, 9)) for _  in range(length))
    return code


def create_otp(user, verify_purpose):
    raw_code = generate_otp(6)
    hash_code = make_password(raw_code)

    OTPVerifyModel.objects.filter(user=user, purpose=verify_purpose, is_valid=True).update(is_valid=False) # invalidate  all  existing  otps with the same purpose
    otp_instance = OTPVerifyModel.objects.create(
        user = user,
        purpose = verify_purpose,
        hash_otp = hash_code
    )

    return raw_code, otp_instance.id


def send_otp_mail(user_name, user_email, raw_code, verify_purpose):

    context = {
        "user_name": user_name,
        "user_email": user_email,
        "raw_code": raw_code,
        "verify_purpose": verify_purpose
    }

    html_message = render_to_string("messages/otp_message.html", context=context)

    send_mail(
        subject=f"Email verification for {verify_purpose}",
        message=f"Dear {user_name},\nYour OTP code is: {raw_code}. It expires in 5 minutes.",
        from_email= None,
        recipient_list=[user_email],
        html_message=html_message,
        fail_silently=False,
    )



def verify_otp(input_otp, otp_instance):
    if otp_instance.is_expired():
        return (False, "OTP is expired.")

    if otp_instance.attempts >= 5:
        return (False, "Max number of attempts reached.")
    
    otp_instance.add_attempt()

    if not check_password(input_otp, otp_instance.hash_otp):
        return (False, "Invalid OTP. Verification is not completed.")
    
    otp_instance.mark_verified()
    return (True, "OTP verified successfully.")



def send_password_reset_mail(email, name, url):
    context = {
        "user_name": name,
        "reset_url": url
    }

    html_message = render_to_string("messages/reset_message.html", context=context)

    send_mail(
        subject="Staff Password Reset",
        message=f"Dear {name},\nYour password url is: {url}. Use it to reset your password it expires in 1 hour.",
        from_email= None,
        recipient_list=[email],
        html_message=html_message,
        fail_silently=False,
    )


def send_email_change_mails(user_name, current_email, new_email, change_url, revert_url):
    context = {
        "user_name": user_name,
        "current_email": current_email,
        "new_email": new_email,
        "url": revert_url,
    }


    revert_html = render_to_string("messages/email_change_notice_message.html", context=context)
    context["url"] = change_url 
    change_html = render_to_string("messages/email_change_confirm_message.html", context=context)


    expiry_hours = "24hrs"

    send_mail(
        subject="Email change initiated on your staff account",
        message=f"Dear {user_name},\n\nAn email change has been initiated on your staff account. A link to complete the change has been sent to the new address below. Until it is completed, your current email stays active on your account.\n\nCurrent email: {current_email}\nNew email: {new_email}\n\nIf this was you, you can ignore this message. No action is needed here.\n\nIf this was not you, open the link below to revert the change and keep your current email:\n{revert_url}\n\nThis link expires in {expiry_hours} hours and can only be used once.\n\nNever forward this email to anyone, because the link controls changes on your account.\n\nYou are receiving this because an email change was initiated for this email address.\n",
        from_email= None,
        recipient_list=[current_email],
        html_message=revert_html,
        fail_silently=False,
    )

    send_mail(
        subject="Confirm your new email address",
        message=f"Dear {user_name},\n\nAn email change has been initiated for your staff account. Once you complete it, this address will replace your current one and you will use it to sign in.\n\nFrom: {current_email}\nTo: {new_email}\n\nTo complete the change, open the link below:\n{change_url}\n\nThis link expires in {expiry_hours} hours and can only be used once.\n\nIf you did not expect this email, you can ignore it and nothing will change. Never forward this email to anyone, because the link completes a change on your account.\n\nYou are receiving this because this email address was entered in an email change request.\n",
        from_email= None,
        recipient_list=[new_email],
        html_message=change_html,
        fail_silently=False,
    )


