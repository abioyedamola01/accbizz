import uuid
from django.shortcuts import (
    render, 
    redirect
)
from django.contrib.auth import  (
    authenticate, 
    login
    )
from .models import OTPVerifyModel
from .forms import (
    StaffLoginForm,
    VerifyOTPForm,
)
from .otp_utils import (
    CreateOTP,
    SendOTPEmail,
    VerifyOTP
)





def StaffLoginView(request):
    if request.user.is_authenticated:
        return redirect("staff_dashboard")


    form = StaffLoginForm(request.POST or None)

    if request.POST and form.is_valid():
        email = form.cleaned_data["email"]
        password = form.cleaned_data["password"]
        user = authenticate(request, email=email, password=password)
        
        if user is None:
            form.add_error(None, "Inavid email or password. Try again")
        elif not user.is_active:
            form.add_error(None, "Staff is not active at the moment.")
        elif user.is_active and user.is_staff:
            purpose = "staff_login"
            otp, otp_id = CreateOTP(user, purpose)
            SendOTPEmail(user.username, email, otp, purpose)

            request.session["otp_verify_info"] = {
                "user_id": user.id,
                "user_email": email,    
                "otp_id":  otp_id,
                "otp_uuid": str(uuid.uuid4()),
                "purpose": purpose
            }

            return redirect("verify_otp_staff")
        

    return render(request, "staffs/login.html", {
        "login_form": form
    })



def VerifyStaffLoginOTP(request):
    if request.user.is_authenticated:
        return redirect("staff_dashboard")

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
        
        verify_status, verify_comment = VerifyOTP(form.cleaned_data["otp_code"], otp_instance)

        if verify_status:
            request.session.flush()
            login(request, user)
            return redirect("staff_dashboard")

        form.add_error(None, verify_comment)
    return render(request, "staffs/otp.html", {
        "user_email": otp_verify_info["user_email"],
        "otp_uuid": otp_verify_info["otp_uuid"],
        "otp_form": form
    })





def ResendStaffOTPView(request):
    if request.user.is_authenticated:
        return redirect("staff_dashboard")

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
    new_otp, new_otp_id = CreateOTP(user, purpose)
    SendOTPEmail(user.username, user.email, new_otp, purpose)
    otp_verify_info["otp_id"] = new_otp_id
    otp_verify_info["otp_uuid"] = str(uuid.uuid4())
    request.session["otp_verify_info"] = otp_verify_info
    
    return render(request, "staffs/otp.html", {
        "user_email": otp_verify_info["user_email"],
        "otp_uuid": otp_verify_info["otp_uuid"],
        "otp_form": form
    })

