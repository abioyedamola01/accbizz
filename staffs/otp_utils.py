import random
from django.contrib.auth.hashers import (make_password, check_password)
from django.core.mail import send_mail
from .models import OTPVerifyModel
from django.template.loader import render_to_string


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
