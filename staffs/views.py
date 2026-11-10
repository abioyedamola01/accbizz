import os
import uuid
from django.http import Http404
from django.urls import (reverse, is_valid_path,)
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
from dashboard.utils import (toast_json_ok, toast_json_error, check_staff_email, add_staff_token_generator, log_staff_action,)
from .models import (OTPVerifyModel, CustomUserModel, ChangeEmailTrackModel, RevertEmailChangeModel,)
from .forms import (StaffLoginForm, VerifyOTPForm, ChangePasswordForm, PasswordForm, ChangeEmailForm,)
from .utils import (create_otp, send_otp_mail, verify_otp, send_password_reset_mail, change_email_token_generator, send_email_change_mails, delete_staff_sessions, delete_staff_other_sessions,)


def staff_login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard_home")
    
    site_info = model_to_dict(SiteModel.objects.first())

    next_url = request.GET.get("next", None)
    if not next_url: next_url = request.session.get("next_url", None)

    request.session.flush()

    form = StaffLoginForm(request.POST or None)

    if request.POST and form.is_valid():
        email = form.cleaned_data["email"]
        password = form.cleaned_data["password"]

        staff = CustomUserModel.objects.filter(email=email).first()
        user = authenticate(request, email=email, password=password)

        if not staff:
            form.add_error(None, "Invalid email or password. Try again")
        elif not user:
            log_staff_action(staff=staff, code="auth.login", label="Failed login attempt.", is_success=False, failure_reason="Invalid credentials.")
            form.add_error(None, "Invalid email or password. Try again")
        elif not user.is_active:
            log_staff_action(staff=staff, code="auth.login", label="Failed login attempt.", is_success=False, failure_reason="Account is inactive.")
            form.add_error(None, "Staff is not active at the moment.")
        elif user.is_active and user.is_staff_member:
            purpose = "staff_login"
            username = user.profile.username
            otp, otp_id = create_otp(user, purpose)
            
            try:
                send_otp_mail(username, email, otp, verify_purpose="Staff Login")
            except Exception as e:
                log_staff_action(staff=user, code="auth.login", label="Failed login attempt", is_success=False, failure_reason=f"{e}")
                form.add_error(None, "An unexpected error occurred on the server. Please try your request again later")

                return render(request, "staffs/login.html", {"site_info": site_info, "login_form": form,})

            
            request.session["otp_verify_info"] = {
                "user_id": user.id,
                "user_email": email,    
                "otp_id":  otp_id,
                "otp_uuid": str(uuid.uuid4()),
                "purpose": purpose
            }

            request.session["next_url"] = next_url


            log_staff_action(staff=user, code="auth.login", label="Initiated login process and received OTP.", is_success=True)
            return redirect("verify_otp_staff")
        else:
            log_staff_action(staff=staff, code="auth.login", label="Failed login attempt.", is_success=False, failure_reason="User is not a staff member.")
            form.add_error(None, "Not a staff member. Check with the admins to update your status.")
        

    return render(request, "staffs/login.html", {
        "site_info": site_info,
        "login_form": form,
    })



def verify_staff_otp_view(request):
    otp_verify_info =  request.session.get("otp_verify_info", None)
    next_url = request.session.get("next_url", None)

    is_valid_next_url = bool(is_valid_path(str(next_url).split("?", maxsplit=1)[0], urlconf=None))

    
    if not otp_verify_info:
        request.session.flush()
        return redirect("staff_login")

    if request.user.is_authenticated and (otp_verify_info["purpose"] == "staff_login"):
        return redirect("dashboard_home")

    otp_instance = OTPVerifyModel.objects.select_related("user").filter(id=otp_verify_info["otp_id"], purpose=otp_verify_info["purpose"], is_valid=True).first()

    
    site_info = model_to_dict(SiteModel.objects.first())
        
    form = VerifyOTPForm(request.POST or None)


    if request.POST and form.is_valid():
        if not otp_instance:
            request.session.pop("otp_verify_info", None)
            return redirect("main_home")

        user = otp_instance.user
        
        verify_status, verify_comment = verify_otp(form.cleaned_data["otp_code"], otp_instance)
        redirect_urls = {
            "staff_login": next_url if is_valid_next_url else "dashboard_home",
            "staff_change_password": "staff_change_password"
        }

        if verify_status:
            if otp_verify_info["purpose"] == "staff_login":
                request.session.flush()
                login(request, user)
                delete_staff_other_sessions(request=request, staff=user)
                log_staff_action(staff=user, code="auth.otp.verify", label="Logged in successfully via OTP.", is_success=True)
            else:
                log_staff_action(staff=user, code="auth.otp.verify", label=f"Verified OTP for {otp_verify_info['purpose']}.", is_success=True)
                
            return redirect(redirect_urls[otp_verify_info["purpose"]])

        log_staff_action(staff=user, code="auth.otp.verify", label="Failed to verify OTP.", is_success=False, failure_reason=verify_comment)
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

    otp_verify_info["otp_id"] = new_otp_id
    otp_verify_info["otp_uuid"] = str(uuid.uuid4())
    request.session["otp_verify_info"] = otp_verify_info

    try:
        send_otp_mail(user.profile.username, user.email, new_otp, verify_purpose=otp_instance.purpose)
        log_staff_action(staff=user, code="auth.otp.resend", label=f"Requested a new OTP for {otp_instance.purpose}.", is_success=True)
    except Exception as e:
        log_staff_action(staff=user, code="auth.otp.resend", label="Failed otp resend attempt", is_success=False, failure_reason=f"{e}")
        form.add_error(None, "An unexpected error occurred on the server. Please try your request again later")


    return render(request, "staffs/otp.html", {
        "site_info": site_info,
        "user_email": otp_verify_info["user_email"],
        "otp_uuid": otp_verify_info["otp_uuid"],
        "otp_form": form,
        "verify_purpose": otp_verify_info["purpose"]
    })



@login_required
def staff_logout_view(request):
    staff = request.user # Capture the user before the session is flushed
    request.session.flush()
    logout(request)
    log_staff_action(staff=staff, code="auth.logout", label="Logged out of the system.", is_success=True)
    return redirect("staff_login")



@login_required
def verify_for_staff_change_password_view(request):
    user = request.user
    purpose = "staff_change_password"
    username = user.profile.username
    email = user.email

    otp, otp_id = create_otp(user, purpose)

    try:
        send_otp_mail(username, email, otp, verify_purpose=purpose)
    except Exception as e:
        log_staff_action(staff=user, code="auth.password_change.initiate_otp", label="Failed password change attempt", is_success=False, failure_reason=f"{e}")
        return render(request, "errors/500.html", status=500)

        
    request.session["otp_verify_info"] = {
        "user_id": user.id,
        "user_email": email,    
        "otp_id":  otp_id,
        "otp_uuid": str(uuid.uuid4()),
        "purpose": purpose
    }
    
    log_staff_action(staff=user, code="auth.password_change.initiate_otp", label="Initiated OTP verification for password change.", is_success=True)

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
            log_staff_action(staff=request.user, code="profile.password_change", label="Failed to change password.", is_success=False, failure_reason="Incorrect current password.")
            password_form.add_error(None, "Incorrect password.")
            return render(request, "staffs/change_password.html", context)

        user.change_password(new_password=new_password)
        log_staff_action(staff=request.user, code="profile.password_change", label="Changed their account password.", is_success=True)

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

        try:
            send_password_reset_mail(email=staff.email, name=staff.profile.username, url=reset_link)
            log_staff_action(staff=request.user, code="auth.password_reset.initiate", label=f"Initiated a password reset for staff: {staff.email}.", is_success=True)
        except Exception as e:
            log_staff_action(staff=user, code="auth.password_reset.initiate", label=f"Failed to initiate a password reset for staff: {staff.email}", is_success=False, failure_reason=f"{e}")
            return toast_json_error("An unexpected error occurred on the server. Please try your request again later")

        return toast_json_ok("Password reset link sent successfully.")

    return toast_json_error("Can't send reset link. Try again later.")



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
        log_staff_action(staff=staff, code="auth.password_reset.complete", label="Reset their password using an email reset link.", is_success=True)

        return toast_json_ok("Password reset successfully.")

    

    return render(request, "staffs/reset_password.html", context)




@login_required
@permission_required(("staffs.manage_staffs", "staffs.change_email",), raise_exception=True)
def change_email_view(request):
    change_email_form = ChangeEmailForm(request.POST or None)
    
    if request.POST and change_email_form.is_valid():
        current_email = change_email_form.cleaned_data["current_email"]
        new_email = change_email_form.cleaned_data["new_email"]

        if check_staff_email(email=new_email):
            return toast_json_error("Can't initiate change, new email is being used by another staff.")

        staff = CustomUserModel.objects.filter(email=current_email).first()

        if not staff:
            return toast_json_error("Can't initiate change, staff does not exist")
        
        # void all existing change email tracks
        ChangeEmailTrackModel.objects.filter(staff=staff, is_valid=True).update(is_valid=False)

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

        try:
            send_email_change_mails(user_name=staff.profile.username, current_email=current_email, new_email=new_email, change_url=change_url, revert_url=revert_url)
            log_staff_action(staff=request.user, code="profile.email_change.initiate", label=f"Initiated email change for staff from {current_email} to {new_email}.", is_success=True)
            
            return toast_json_ok("Email change process initiated successfully.")
        except:
            return toast_json_error("Email change process could not be initiated. Please try again later.")

    print(change_email_form.errors.as_json())
    return toast_json_error("Email change process could not be initiated.", form_errors=change_email_form.errors.as_json())
    



@login_required
@permission_required(("staffs.manage_staffs", "staffs.remove_user",), raise_exception=True)
def remove_staff_view(request, email):
    staff = CustomUserModel.objects.filter(email=email).first()

    if not staff:
        log_staff_action(staff=request.user, code="staff.remove", label="Failed to remove staff member.", is_success=False, failure_reason=f"Staff does not exist ({email}).")
        return toast_json_error("Can't remove staff.", error="staff does not exist")

    if not staff.is_staff_member:
        log_staff_action(staff=request.user, code="staff.remove", label="Failed to remove staff member.", is_success=False, failure_reason="Attempted to remove a user who is not marked as a staff member.")
        return toast_json_error("Can't remove staff.", error="user has been set to not a staff")

    delete_staff_sessions(staff)
    staff.remove_as_staff()
    log_staff_action(staff=request.user, code="staff.remove", label=f"Removed staff privileges for: {staff.email}.", is_success=True)

    return toast_json_ok("Staff removed successfully.")


@login_required
@permission_required(("staffs.manage_staffs", "staffs.reinstate_user",), raise_exception=True)
def reinstate_staff_view(request, email):
    staff = CustomUserModel.objects.filter(email=email).first()

    if not staff:
        log_staff_action(staff=request.user, code="staff.reinstate", label="Failed to reinstate staff member.", is_success=False, failure_reason=f"Staff does not exist ({email}).")
        return toast_json_error("Can't reinstate staff.", error="staff does not exist")

    if staff.is_staff_member:
        log_staff_action(staff=request.user, code="staff.reinstate", label="Failed to reinstate staff member.", is_success=False, failure_reason="Attempted to reinstate a user who is already an active staff member.")
        return toast_json_error("Can't reinstate staff.", error="staff has been a staff member")

    staff.reinstate_as_staff()
    log_staff_action(staff=request.user, code="staff.reinstate", label=f"Reinstated staff privileges for: {staff.email}.", is_success=True)

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
                log_staff_action(staff=staff, code="profile.email_change.complete", label=f"Finalized email change to {change_email_track.new_email}.", is_success=True)

                context["status"] = "success"

            else:
                log_staff_action(staff=staff, code="profile.email_change.complete", label="Failed to finalize email change.", is_success=False, failure_reason="Incorrect password.")
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
                log_staff_action(staff=staff, code="profile.email_revert", label=f"Reverted email change back to {change_email_track.current_email}.", is_success=True)

                context["status"] = "success"
            else:
                log_staff_action(staff=staff, code="profile.email_revert", label="Failed to revert email change.", is_success=False, failure_reason="Incorrect password.")
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
        "name": creation_track.username,
        "password_form": password_form
    }

    if request.POST and password_form.is_valid():
        info = creation_track.get_info()
        email = info["email"]
        role = info["role"]
        first_name = info.get("first_name", "")
        last_name = info.get("last_name", "")

        try:
            staff_details = {
                "email": email,
                "password": password_form.cleaned_data["password"],
                "is_staff_member": True,
                "is_admin": role == "admin"
            }
            
            staff = CustomUserModel.objects.create(**staff_details)
            staff.profile.role = role
            if role != "admin":
                staff.profile.first_name = first_name
                staff.profile.last_name = last_name
            staff.profile.save(update_fields=("role", "first_name", "last_name",))
            
            admin_group = Group.objects.get(name=f"{info['role']}_group")
            admin_group.user_set.add(staff)

            creation_track.set_used()
            log_staff_action(staff=staff, code="staff.account.create", label="Created their new staff account via invitation link.", is_success=True)

            context["status"] = "success"
        except Exception as e:
            print(e)

    return render(request, "staffs/create_new_account.html", context)