import uuid
from django.shortcuts import (render, redirect)
from django.contrib.auth import (authenticate, login,logout)
from django.contrib.auth.decorators import login_required
from django.forms.models import model_to_dict
from dashboard.models import SiteModel
from .models import OTPVerifyModel
from .forms import (StaffLoginForm, VerifyOTPForm,)
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
            print("WD")
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



def verify_staff_login_otp_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard_home")
    
    site_info = model_to_dict(SiteModel.objects.first())

    otp_verify_info =  request.session.get("otp_verify_info", None)
    if not otp_verify_info:
        request.session.flush()
        return redirect("home")

    form = VerifyOTPForm(request.POST or None)

    if request.POST and form.is_valid():
        otp_instance = OTPVerifyModel.objects.select_related("user").filter(id=otp_verify_info["otp_id"], purpose=otp_verify_info["purpose"], is_valid=True).first()
        if not otp_instance:
            request.session.flush()
            return redirect("home")

        user = otp_instance.user
        
        verify_status, verify_comment = verify_otp(form.cleaned_data["otp_code"], otp_instance)

        if verify_status:
            request.session.flush()
            login(request, user)
            return redirect("dashboard_home")

        form.add_error(None, verify_comment)
    return render(request, "staffs/otp.html", {
        "site_info": site_info,
        "user_email": otp_verify_info["user_email"],
        "otp_uuid": otp_verify_info["otp_uuid"],
        "otp_form": form
    })





def resend_staff_otp_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard_home")
    
    site_info = model_to_dict(SiteModel.objects.first())

    otp_verify_info = request.session.get("otp_verify_info", None)
    if not otp_verify_info:
        return redirect("staff_login")
    
    otp_instance = OTPVerifyModel.objects.select_related("user").filter(id=otp_verify_info["otp_id"], purpose=otp_verify_info["purpose"], is_valid=True).first()
    if not otp_instance:
        request.session.flush()
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
        "otp_form": form
    })



@login_required
def staff_logout_view(request):
    request.session.flush()
    logout(request)
    return redirect("home")

