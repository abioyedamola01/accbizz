from django.shortcuts import render, redirect
from django.contrib.auth.decorators import (
    login_required,
    permission_required
)
from django.forms.models import model_to_dict
from .forms import (
    EditProfileForm,
    UpdateAvatarForm
)


# Create your views here.
@login_required()
@permission_required("staffs.view_dahboard", raise_exception=True)
def DashboardHomeView(request):
    return render(request, "dashboard/home.html", {})


@login_required
@permission_required("staffs.view_dashboard", raise_exception=True)
def ProfileView(request):
    profile_form = EditProfileForm(request.POST or None, instance=request.user.profile)
    avatar_form = UpdateAvatarForm()
    profile = request.user.profile
    profile_info = list()
    for field, value in model_to_dict(profile).items():
        if field not in ("id", "avatar",):
            field_name = str(field).replace("_", " ").title()
            if field == "role":
                value = profile.get_role_display()
            if field == "gender":
                value = profile.get_gender_display()

            profile_info.append((field_name, value))

    context = {
        "current": "communication",
        "profile_info": profile_info,
        "profile_form": profile_form,
        "avatar_form":  avatar_form
    }
    return render(request, "dashboard/profile.html", context)




@login_required
@permission_required("staffs.view_dashboard", raise_exception=True)
def UpdateProfileAvatarView(request):
    avatar_form = UpdateAvatarForm(request.POST or None, request.FILES or None)

    if request.POST and avatar_form.is_valid():
        avatar_form = UpdateAvatarForm(request.POST, request.FILES, instance=request.user.profile)
        avatar_form.save()

    return redirect("dashboard_profile")


@login_required
@permission_required("staffs.view_dashboard", raise_exception=True)
def UpdateProfileInfoView(request):
    profile_edit_form = EditProfileForm(request.POST or None)

    if request.POST and profile_edit_form.is_valid():
        profile_edit_form = EditProfileForm(request.POST, instance=request.user.profile)
        profile_edit_form.save()

    return redirect("dashboard_profile")