import uuid
from django.shortcuts import (render, redirect)
from django.contrib.auth import (authenticate, login, logout,)
from django.contrib.auth.decorators import login_required
from django.forms.models import model_to_dict
from dashboard.models import SiteModel
from .models import OTPVerifyModel, CustomUserModel
from .forms import (StaffLoginForm, VerifyOTPForm, ChangePasswordForm)
from .otp_utils import (create_otp, send_otp_mail, verify_otp,)





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
    if not otp_verify_info:
        request.session.flush()
        return redirect("main_home")

    if request.user.is_authenticated and (otp_verify_info["purpose"] == "staff_login"):
        return redirect("dashboard_home")

    
    site_info = model_to_dict(SiteModel.objects.first())
    

    form = VerifyOTPForm(request.POST or None)


    if request.POST and form.is_valid():
        otp_instance = OTPVerifyModel.objects.select_related("user").filter(id=otp_verify_info["otp_id"], purpose=otp_verify_info["purpose"], is_valid=True).first()
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