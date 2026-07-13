from django.conf import settings
import random
from django.contrib.auth.hashers import (
    make_password,
    check_password
)
from django.contrib.auth import (
    authenticate,
    login
)
from django.core.mail import send_mail
from django.conf import settings
from .models import OTPVerifyModel


def GenerateOTP(length=6):
    code = "".join(str(random.randint(0, 9)) for _  in range(length))
    return code


def CreateOTP(user, verify_purpose):
    raw_code = GenerateOTP(6)
    hash_code = make_password(raw_code)

    OTPVerifyModel.objects.filter(user=user, purpose=verify_purpose, is_valid=True).update(is_valid=False) # invalidate  all  existing  otps with the same purpose
    otp_instance = OTPVerifyModel.objects.create(
        user = user,
        purpose = verify_purpose,
        hash_otp = hash_code
    )

    return raw_code, otp_instance.id


def SendOTPEmail(user_name, user_email, raw_code, verify_purpose):
    send_mail(
        subject=f"Email verification for {verify_purpose}",
        message=f"Dear {user_name},\nYour OTP code is: {raw_code}. It expires in 5 minutes.",
        from_email= None,
        recipient_list=[user_email],
        fail_silently=False,
    )



def VerifyOTP(input_otp, otp_instance):
    if otp_instance.is_expired():
        otp_instance.invalidate_otp()
        return (False, "OTP is expired.")

    if otp_instance.attempts >= 5:
        otp_instance.invalidate_otp()
        return (False, "Max number of attempts reached.")
    
    otp_instance.add_attempt()

    if not check_password(input_otp, otp_instance.hash_otp):
        return (False, "Invalid OTP. Verification is not completed.")
    
    otp_instance.mark_verified()
    return (True, "OTP verified successfully.")
