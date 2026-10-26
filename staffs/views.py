import os
import uuid
from django.http import Http404
from django.urls import reverse
from django.shortcuts import (render, redirect)
from django.contrib.auth import (authenticate, login, logout,)
from django.contrib.auth.decorators import (login_required, permission_required,)
from django.contrib.auth.tokens import (PasswordResetTokenGenerator, default_token_generator,)
from django.contrib.auth.models import Group
from django.forms.models import model_to_dict
from django.contrib.sites.shortcuts import get_current_site
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import (urlsafe_base64_encode, urlsafe_base64_decode,)
from django.utils.crypto import get_random_string
from dashboard.models import (SiteModel, AddStaffModel,)
from dashboard.utils import (toast_json_ok, toast_json_error, add_staff_token_generator,)
from .models import (OTPVerifyModel, CustomUserModel, ChangeEmailTrackModel, RevertEmailChangeModel,)
from .forms import (StaffLoginForm, VerifyOTPForm, ChangePasswordForm, PasswordForm, ChangeEmailForm,)
from .utils import (create_otp, send_otp_mail, verify_otp, send_password_reset_mail, change_email_token_generator, send_email_change_mails, delete_staff_sessions, delete_staff_other_sessions,)





def staff_login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard_home")
    
    site_info = model_to_dict(SiteModel.objects.first())

    request.session.flush()
    form = StaffLoginForm(request.POST or None)

    if request.POST and form.is_valid():
        email = form.cleaned_data["email"]
        password = form.cleaned_data["password"]
        user = authenticate(request, email=email, password=password)
        
        if not user:
            form.add_error(None, "Inavid email or password. Try again")
        elif not user.is_active:
            form.add_error(None, "Staff is not active at the moment.")
        elif user.is_active and user.is_staff_member:
            purpose = "staff_login"
            username = user.profile.get_username()
            otp, otp_id = create_otp(user, purpose)
            send_otp_mail(username, email, otp, verify_purpose="Staff Login")

            request.session["otp_verify_info"] = {
                "user_id": user.id,
                "user_email": email,    
                "otp_id":  otp_id,
                "otp_uuid": str(uuid.uuid4()),
                "purpose": purpose
            }

            return redirect("verify_otp_staff")
        else:
            form.add_error(None, "Not a staff member. Check with the admins to update your status.")
        

    return render(request, "staffs/login.html", {
        "site_info": site_info,
        "login_form": form,
    })



def verify_staff_otp_view(request):
    otp_verify_info =  request.session.get("otp_verify_info", None)
    print(otp_verify_info)
    if not otp_verify_info:
        request.session.flush()
        return redirect("main_home")

    if request.user.is_authenticated and (otp_verify_info["purpose"] == "staff_login"):
        return redirect("dashboard_home")

    otp_instance = OTPVerifyModel.objects.select_related("user").filter(id=otp_verify_info["otp_id"], purpose=otp_verify_info["purpose"], is_valid=True).first()

    if otp_instance and otp_instance.is_expired():
        request.session.pop("otp_verify_info", None)
        return redirect("main_home")
    
    site_info = model_to_dict(SiteModel.objects.first())
        
    form = VerifyOTPForm(request.POST or None)


    if request.POST and form.is_valid():
        # otp_instance = OTPVerifyModel.objects.select_related("user").filter(id=otp_verify_info["otp_id"], purpose=otp_verify_info["purpose"], is_valid=True).first()
        if not otp_instance:
            request.session.pop("otp_verify_info", None)
            return redirect("main_home")

        user = otp_instance.user
        
        verify_status, verify_comment = verify_otp(form.cleaned_data["otp_code"], otp_instance)
        redirect_urls = {
            "staff_login": "dashboard_home",
            "staff_change_password": "staff_change_password"
        }

        if verify_status:
            if otp_verify_info["purpose"] == "staff_login":
                request.session.flush()
                login(request, user)
                delete_staff_other_sessions(request=request, staff=user)
            return redirect(redirect_urls[otp_verify_info["purpose"]])

        form.add_error(None, verify_comment)
    return render(request, "staffs/otp.html", {
        "site_info": site_info,
        "user_email": otp_verify_info["user_email"],
        "otp_uuid": otp_verify_info["otp_uuid"],
        "otp_form": form,
        "verify_purpose": otp_verify_info["purpose"]
    })





def resend_staff_otp_view(request):
    otp_verify_info = request.session.get("otp_verify_info", None)
    if not otp_verify_info:
        return redirect("staff_login")

    if request.user.is_authenticated and otp_verify_info["purpose"] == "staff_login":
        return redirect("dashboard_home")
    
    site_info = model_to_dict(SiteModel.objects.first())

    otp_verify_info = request.session.get("otp_verify_info", None)
    if not otp_verify_info:
        return redirect("staff_login")
    
    otp_instance = OTPVerifyModel.objects.select_related("user").filter(id=otp_verify_info["otp_id"], purpose=otp_verify_info["purpose"], is_valid=True).first()
    if not otp_instance:
        request.session.pop("otp_verify_info", None)
        return redirect("staff_login")
        
    form = VerifyOTPForm()
    purpose = otp_verify_info["purpose"]
    user = otp_instance.user
    
    otp_instance.invalidate_otp()
    new_otp, new_otp_id = create_otp(user, purpose)
    send_otp_mail(user.profile.get_username(), user.email, new_otp, verify_purpose=otp_instance.get_purpose_display())
    otp_verify_info["otp_id"] = new_otp_id
    otp_verify_info["otp_uuid"] = str(uuid.uuid4())
    request.session["otp_verify_info"] = otp_verify_info
    
    return render(request, "staffs/otp.html", {
        "site_info": site_info,
        "user_email": otp_verify_info["user_email"],
        "otp_uuid": otp_verify_info["otp_uuid"],
        "otp_form": form,
        "verify_purpose": otp_verify_info["purpose"]
    })



@login_required
def staff_logout_view(request):
    request.session.flush()
    logout(request)
    return redirect("staff_login")



@login_required
def verify_for_staff_change_password_view(request):
    user = request.user
    purpose = "staff_change_password"
    username = user.profile.get_username()
    email = user.email

    otp, otp_id = create_otp(user, purpose)
    send_otp_mail(username, email, otp, verify_purpose=purpose)

    request.session["otp_verify_info"] = {
        "user_id": user.id,
        "user_email": email,    
        "otp_id":  otp_id,
        "otp_uuid": str(uuid.uuid4()),
        "purpose": purpose
    }

    return redirect("verify_otp_staff")


@login_required
def staff_change_password_view(request):
    otp_verify_info = request.session.get("otp_verify_info")

    if otp_verify_info and otp_verify_info["purpose"] == "staff_change_password":
        pass

    else:
        return redirect("staff_verify_staff_change_password")

    otp_instance = OTPVerifyModel.objects.filter(user=request.user, id=otp_verify_info["otp_id"], purpose="staff_change_password", verified=True,).first()
    
    if (not otp_instance) or otp_instance.is_expired(): 
        return redirect("staff_verify_staff_change_password")


    password_form = ChangePasswordForm(request.POST or None)


    context = {
        "form": password_form
    }


    if request.POST and password_form.is_valid():
        old_password = password_form.cleaned_data["old_password"]
        new_password = password_form.cleaned_data["new_password"]

        user = authenticate(request, email=request.user.email, password=old_password)

        if not user:
            password_form.add_error(None, "Incorrect password.")

            return render(request, "staffs/change_password.html", context)

        user.change_password(new_password=new_password)

        context["success"] = True
        

    return render(request, "staffs/change_password.html", context)


@login_required
@permission_required(("staffs.manage_staffs", "staffs.reset_user_password",), raise_exception=True)
def reset_staff_password_view(request, user):
    staff = CustomUserModel.objects.select_related("profile",).filter(email=user).first()
    staff.last_login = timezone.now() # to void all existing tokens
    staff.save()

    if staff:
        idb64 = urlsafe_base64_encode(force_bytes(staff.id))
        token = PasswordResetTokenGenerator().make_token(staff)

        base_url = os.getenv("BASE_URL")
        reset_link = f"{base_url}/users/staffs/accounts/auth/reset-password/use/{idb64}/{token}"

        send_password_reset_mail(email=staff.email, name=staff.profile.get_username(), url=reset_link)

        return toast_json_ok("Password reset link sent successfully.")

    return toast_json_error("Can't send reset link.")



def use_reset_staff_password_link_view(request, idb64, token):
    id = urlsafe_base64_decode(idb64).decode()
    staff = CustomUserModel.objects.filter(id=id).first()

    if not (staff and PasswordResetTokenGenerator().check_token(staff, token)):
        raise Http404()


    reset_form = PasswordForm(request.POST or None)

    context = {
        "reset_form": reset_form
    }


    if request.POST and reset_form.is_valid():
        new_password = reset_form.cleaned_data["password"]

        staff.set_password(new_password)
        staff.save()

        return toast_json_ok("Password reset successfully.")

    

    return render(request, "staffs/reset_password.html", context)




@login_required
@permission_required(("staffs.manage_staffs", "staffs.change_email",), raise_exception=True)
def change_email_view(request):
    change_email_form = ChangeEmailForm(request.POST or None)

    if request.POST and change_email_form.is_valid():
        current_email = change_email_form.cleaned_data["current_email"]
        new_email = change_email_form.cleaned_data["new_email"]

        staff = CustomUserModel.objects.filter(email=current_email).first()

        if not staff:
            return toast_json_error("Can't initiate change, staff does not exist")

        # void all existing change email tracks
        existing_change_email_tracks = ChangeEmailTrackModel.objects.filter(staff=staff, is_valid=True)
        for track in existing_change_email_tracks:
            track.invalidate()

        change_email_track = ChangeEmailTrackModel.objects.create(initiated_by=request.user, staff=staff, new_email=new_email, current_email=current_email)
        change_token = change_email_token_generator.make_token(change_email_track)

        staff_revert_email_change, is_created = RevertEmailChangeModel.objects.get_or_create(staff=staff)
        
        if not is_created:
            staff_revert_email_change.save(update_fields=("last_updated",)) # invalidate any existing token

        revert_token = change_email_token_generator.make_token(staff_revert_email_change)
        
        staff_idb64 = urlsafe_base64_encode(force_bytes(staff.id))
        track_idb64 = urlsafe_base64_encode(force_bytes(change_email_track.id))

        base_url = os.getenv("BASE_URL")
        
        change_url = f"{base_url}/users/staffs/accounts/change-email/{get_random_string(length=13).lower()}/{track_idb64}/{staff_idb64}/{change_token}"
        revert_url = f"{base_url}/users/staffs/accounts/change-email/{get_random_string(length=13).lower()}/{track_idb64}/{staff_idb64}/{revert_token}/revert-change"

        send_email_change_mails(user_name=staff.profile.get_username(), current_email=current_email, new_email=new_email, change_url=change_url, revert_url=revert_url)

    return toast_json_ok("Email change process initiated successfully.")



@login_required
@permission_required(("staffs.manage_staffs", "staffs.remove_user",), raise_exception=True)
def remove_staff_view(request, email):
    staff = CustomUserModel.objects.filter(email=email).first()

    if not staff:
        return toast_json_error("Can't remove staff.", error="staff does not exist")

    if not staff.is_staff_member:
        return toast_json_error("Can't remove staff.", error="user has been set to not a staff")

    delete_staff_sessions(staff)
    staff.remove_as_staff()

    return toast_json_ok("Staff removed successfully.")


@login_required
@permission_required(("staffs.manage_staffs", "staffs.reinstate_user",), raise_exception=True)
def reinstate_staff_view(request, email):
    staff = CustomUserModel.objects.filter(email=email).first()

    if not staff:
        return toast_json_error("Can't reinstate staff.", error="staff does not exist")

    if staff.is_staff_member:
        return toast_json_error("Can't reinstate staff.", error="staff has been a staff member")

    staff.reinstate_as_staff()

    return toast_json_ok("Staff reinstated successfully.")




def finish_email_change_view(request, track_idb64, staff_idb64, token, *args, **kwargs):
    try:
        id = urlsafe_base64_decode(staff_idb64).decode("utf-8")
        track_id = urlsafe_base64_decode(track_idb64).decode("utf-8")
    except:
        raise Http404

    staff = CustomUserModel.objects.filter(id=id).first()
    if not staff:
        raise Http404 

    change_email_track = staff.change_email_track.filter(id=track_id).first()
    
    if not change_email_track:
        raise Http404
    
    if change_email_track.is_reverted:
        context = {"status": "reverted"}
        return render(request, "staffs/finish_change_email.html", context)
    
    if change_email_track.is_changed:
        context = {"status": "changed"}
        return render(request, "staffs/finish_change_email.html", context)

    if change_email_track.is_expired:
        context = {"status": "expired"}
        return render(request, "staffs/finish_change_email.html", context)

       

    context = {
        "current_email": change_email_track.current_email,
        "new_email": change_email_track.new_email
    }


    if change_email_token_generator.check_token(change_email_track, token):
        form = PasswordForm(request.POST or None)

        context["form"] = form

        
        if request.POST and form.is_valid():
            if authenticate(request, username=staff.email, password=form.cleaned_data["password"]):
                staff.email = change_email_track.new_email
                staff.save()
                change_email_track.mark_changed()
                delete_staff_sessions(staff=staff) # logout staff everywhere to force login with new email  

                context["status"] = "success"

            else:
                form.add_error("password", "Invalid password")
    else:
        context = {"status": "invalid_token"}


    return render(request, "staffs/finish_change_email.html", context)
    
    





def revert_email_change_view(request, track_idb64, staff_idb64, token, *args, **kwargs):
    try:
        id = urlsafe_base64_decode(staff_idb64).decode("utf-8")
        track_id = urlsafe_base64_decode(track_idb64).decode("utf-8")
    except:
        raise Http404
    
    staff = CustomUserModel.objects.filter(id=id).first()
    if not staff:
        raise Http404 

    change_email_track = staff.change_email_track.filter(id=track_id).first()
    
    if not change_email_track:
        raise Http404
    
    if change_email_track.is_reverted:
        context = {"status": "reverted"}
        return render(request, "staffs/revert_change_email.html", context)
    
    if change_email_track.is_expired:
        context = {"status": "expired"}
        return render(request, "staffs/revert_change_email.html", context)

    context = {
        "current_email": change_email_track.current_email,
        "new_email": change_email_track.new_email
    }


    if change_email_token_generator.check_token(staff.revert_email_change, token):
        form = PasswordForm(request.POST or None)
        context["form"] = form

        if request.POST and form.is_valid():
            if authenticate(request, username=staff.email, password=form.cleaned_data["password"]):
                staff.email = change_email_track.current_email
                staff.save()
                change_email_track.mark_reverted()
                delete_staff_sessions(staff=staff)

                context["status"] = "success"
            else:
                form.add_error("password", "Invalid password")

    else:
        context = {"status": "invalid_token"}
        
        
    return render(request, "staffs/revert_change_email.html", context)
            




def new_staff_account_creation_view(request, idb64, token):
    try:
        track_id = int(urlsafe_base64_decode(idb64).decode("utf-8"))
    except:
        raise Http404


    creation_track = AddStaffModel.objects.filter(id=track_id).first()

    if not creation_track:
        raise Http404
 

    if creation_track.is_expired:
        context = {"status": "is_expired"}
        return render(request, "staffs/create_new_account.html", context)


    if creation_track.is_used:
        context = {"status": "is_used"}
        return render(request, "staffs/create_new_account.html", context)


    if not add_staff_token_generator.check_token(creation_track, token):
        context = {"status": "invalid_token"}
        return render(request, "staffs/create_new_account.html", context)


    password_form = PasswordForm(request.POST or None)

    context = {
        "name": creation_track.get_username(),
        "password_form": password_form
    }

    if request.POST and password_form.is_valid():
        info = creation_track.get_info()

        try:
            staff = CustomUserModel.objects.create(email=info["email"], password=password_form.cleaned_data["password"], is_staff_member=True, is_admin=False)
            staff.profile.role = info["role"]
            staff.profile.first_name = info["first_name"]
            staff.profile.last_name = info["last_name"]
            staff.profile.save(update_fields=("role", "first_name", "last_name",))
            
            admin_group = Group.objects.get(name=f"{info["role"]}_group")
            admin_group.user_set.add(staff)

            creation_track.set_used()

            context["status"] = "success"
        except:
            pass

    return render(request, "staffs/create_new_account.html", context)