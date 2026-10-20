from django.http import JsonResponse
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import send_mail
from django.template.loader import render_to_string
from .models import AddStaffModel



def toast_json_ok(message, status=200, *args, **kwargs):
    load = {
        "ok": True,
        "message": message
    }

    for key, value in kwargs.items():
        load[str(key)] = value

    return JsonResponse(load, status=status)

def toast_json_error(message, status=400, *args, **kwargs):
    load = {
        "ok": False,
        "message": message
    }

    for key, value in kwargs.items():
        load[str(key)] = value

    return JsonResponse(load, status=status)





class AddStaffTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, inst, timestamp):
        value = f"{inst.pk}{timestamp}{inst.email}{inst.is_used}{inst.is_valid}"
        return value

add_staff_token_generator = AddStaffTokenGenerator()


def invalidate_add_staff_tracks(email):
    for track in AddStaffModel.objects.filter(email=email, is_valid=True):
        track.invalidate()


def send_account_creation_email(name, email, url):

    context = {
        "name": name,
        "url": url
    }

    html_message = render_to_string("messages/account_creation_message.html", context=context)

    send_mail(
        subject="Finish creating your staff account",
        message=f"Dear {name},\n\nA staff account has been set up for you. To finish creating it, open the link below and create a new password:\n{url}\n\nThis link expires in 24 hours and can only be used once.\n\nIf you did not expect this email, you can ignore it and no account will be created. Never forward this email to anyone, because the link lets whoever has it set the password for your account.\n\nYou are receiving this because a staff account was set up for this email address.\n",
        from_email= None,
        recipient_list=[email],
        html_message=html_message,
        fail_silently=False,
    )