import os
from datetime import (timedelta, datetime,)
from statistics import mean
from django.shortcuts import (render, redirect,)
from django.urls import reverse
from django.http import JsonResponse
from django.utils.encoding import force_bytes
from django.utils.http import (urlsafe_base64_encode, urlsafe_base64_decode,)
from django.contrib.auth.decorators import (login_required, permission_required,)
from django.db.models import (Q, F, Count, Avg)
from django.forms.models import model_to_dict
from django.template.loader import render_to_string
from django.utils import timezone
from .forms import (EditProfileForm, UpdateAvatarForm, SiteInfoForm, SiteVisualIdentityForm, SiteHomeSectionUpdateFormset, HeroInfoForm, HeroImgForm, AboutForm, TeamForm, FAQForm, ServiceForm, TestimonialForm, StaffForm,)
from .models import (SiteModel, HeroSectionModel, AboutSectionModel, TeamModel, FAQsModel, ServiceModel, TestimonialModel, ContactMessageModel, AddStaffModel)
from staffs.models import (CustomUserModel, UserProfileModel, StaffActionsLogModel,)
from staffs.forms import ChangeEmailForm
from .utils import (toast_json_ok, toast_json_error, check_staff_email, add_staff_token_generator, add_new_staff, log_staff_action, get_staff_actions_logs, get_recent_staff_actions, get_logs_series, invalidate_add_staff_tracks, send_account_creation_email, 
                    get_reports_range, get_change_percent, get_average_response_time, get_enquiries_series, get_enquiries_by_services, get_response_performance, get_busiest_days, get_umami_analytics_data, get_content_health, 
                    get_enquiries_counts, get_items_batch,)



# Create your views here.
@login_required()
@permission_required("staffs.view_dashboard", raise_exception=True)
def dashboard_home_view(request):
    return redirect("dashboard_site")


@login_required
@permission_required("staffs.view_dashboard", raise_exception=True)
def profile_view(request):
    profile_form = EditProfileForm(request.POST or None, instance=request.user.profile)
    avatar_form = UpdateAvatarForm()
    profile = request.user.profile
    profile_info = list()
    for field, value in model_to_dict(profile).items():
        if field not in ("id", "avatar", "last_updated"):
            field_name = str(field).replace("_", " ").title()
            if field == "role":
                value = profile.get_role_display()
            if field == "gender":
                value = profile.get_gender_display()

            profile_info.append((field_name, value))
    

    context = {
        "current": "staff profile",
        "profile_info": profile_info,
        "profile_form": profile_form,
        "avatar_form":  avatar_form
    }
    return render(request, "dashboard/profile.html", context)




@login_required
@permission_required("staffs.view_dashboard", raise_exception=True)
def update_profile_avatar_view(request):
    avatar_form = UpdateAvatarForm(request.POST or None, request.FILES or None)

    if request.POST and avatar_form.is_valid():
        avatar_form = UpdateAvatarForm(request.POST, request.FILES, instance=request.user.profile)
        avatar_form.save()
        
        log_staff_action(staff=request.user, code="profile.avatar.update", label="Updated their profile picture.", is_success=True)
        return toast_json_ok("Profile picture updated successfully.")
    
    if request.POST:
        log_staff_action(staff=request.user, code="profile.avatar.update", label="Failed to update profile picture.", is_success=False, failure_reason="Invalid form data.")
    
    return toast_json_error("Can't update profile picture.", form_errors=avatar_form.errors.as_json())


@login_required
@permission_required("staffs.view_dashboard", raise_exception=True)
def update_profile_info_view(request):
    profile_edit_form = EditProfileForm(request.POST or None)

    if request.POST and profile_edit_form.is_valid():
        profile_edit_form = EditProfileForm(request.POST, instance=request.user.profile)
        profile_edit_form.save()

        log_staff_action(staff=request.user, code="profile.update", label="Updated their profile information.", is_success=True)
        return toast_json_ok("Profile updated successfully.")
    
    if request.POST:
        log_staff_action(staff=request.user, code="profile.update", label="Failed to update profile information.", is_success=False, failure_reason="Invalid form data.")
    
    return toast_json_error("Can't update profile.", form_errors=profile_edit_form.errors.as_json())



@login_required
@permission_required(("staffs.view_dashboard", "staffs.manage_site", "staffs.manage_homepage",), raise_exception=True)
def site_view(request):
    site_info_instance = SiteModel.objects.first()
    site_info_form = SiteInfoForm(request.POST or None, instance=site_info_instance)    
    visual_identity_form = SiteVisualIdentityForm(request.POST or None, instance=site_info_instance)


    context = {
        "current": "site",
        "site_form": site_info_form,
        "visual_identity_form": visual_identity_form,
        "site_info": model_to_dict(site_info_instance),
        "site_info_last_updated": site_info_instance.last_updated,
    }
    return render(request, "dashboard/site.html", context)




@login_required
@permission_required(("staffs.view_dashboard", "staffs.manage_site", ), raise_exception=True)
def update_site_info_view(request):
    site_info = SiteModel.objects.first()
    site_info_form = SiteInfoForm(request.POST or None, instance=site_info)
    
    if request.POST and site_info_form.is_valid():
        site_info_form.save()

        log_staff_action(staff=request.user, code="site.info.update", label="Updated the general site information.", is_success=True)
        return toast_json_ok("Site info updated successfully.")
    
    if request.POST:
        log_staff_action(staff=request.user, code="site.info.update", label="Failed to update general site information.", is_success=False, failure_reason="Invalid form data.")
    return toast_json_error("Can't update site info.", form_errors=site_info_form.errors.as_json())


@login_required
@permission_required(("staffs.view_dashboard", "staffs.manage_site", ), raise_exception=True)
def update_site_visual_identity_view(request):
    site_info_instance = SiteModel.objects.first()  
    visual_identity_form = SiteVisualIdentityForm(request.POST or None, request.FILES or None, instance=site_info_instance)
    
    if request.POST and visual_identity_form.is_valid():
        visual_identity_form.save()

        log_staff_action(staff=request.user, code="site.visuals.update", label="Updated the site's visual identity.", is_success=True)
        return toast_json_ok("Visual identity updated sucessfully.")
    
    if request.POST:
        log_staff_action(staff=request.user, code="site.visuals.update", label="Failed to update site visual identity.", is_success=False, failure_reason="Invalid form data.")
    return toast_json_error("Can't update visual identity.", form_errors=visual_identity_form.errors.as_json())


@login_required
@permission_required(("staffs.view_dashboard", "staffs.manage_site", "staffs.manage_homepage",), raise_exception=True)
def update_site_home_sections_view(request):
    section_formset = SiteHomeSectionUpdateFormset(request.POST or None)
    if request.POST and section_formset.is_valid():
        section_formset.save()

        log_staff_action(staff=request.user, code="site.sections.update", label="Updated the site's homepage sections.", is_success=True)
        return toast_json_ok("Home sections updated successfully.")
    
    if request.POST:
        log_staff_action(staff=request.user, code="site.sections.update", label="Failed to update homepage sections.", is_success=False, failure_reason="Invalid form data.")
    return toast_json_error("Can't update home sections.", form_errors=section_formset.errors)






@login_required
@permission_required(("staffs.manage_contents"), raise_exception=True)
def contents_view(request):
    tab = str(request.GET.get("tab")).lower()
    tab = tab if tab in ["home", "about", "services", "faqs", "testimonials"] else "home"

    context = {}

    if tab == "home":
        site_info_instance = SiteModel.objects.first()
        home_sections = site_info_instance.sections.order_by("order",)
        section_formset = SiteHomeSectionUpdateFormset(request.POST or None, queryset=home_sections)
        

        hero_instance = HeroSectionModel.objects.first()
        hero_form = HeroInfoForm(request.POST or None, instance=hero_instance)
        hero_img_form = HeroImgForm(request.POST or None, instance=hero_instance)

        context = {
            "section_formset": section_formset,
            "hero_form": hero_form,
            "hero_img_form": hero_img_form
        }
    elif tab == "about":
        about_instance = AboutSectionModel.objects.first()
        about_form = AboutForm(request.POST or None, instance=about_instance)
        team_members = about_instance.team.order_by("-id",).filter(is_member=True)
        team_form = TeamForm()

        context = {
            "about_form": about_form,
            "team": team_members,
            "team_form":  team_form,
        }
    elif tab== "services":
        services = ServiceModel.objects.filter().order_by("-id")
        service_form = ServiceForm()
        context = {
            "services": services,
            "service_form": service_form
        }

    elif tab == "faqs":
        faqs = list(FAQsModel.objects.select_related("service").filter().order_by("-id")[:11])
        services = list(ServiceModel.objects.filter().values("id", "title"))

        faq_form = FAQForm()

        context = {
            "faqs": faqs[:10],
            "services": services,
            "faq_form": faq_form
        }

        if len(faqs) == 11:
            context["has_more"] = True
            context["next_batch_point"] = faqs[-1].id


    elif tab == "testimonials":
        testmonials = list(TestimonialModel.objects.filter().order_by("-id")[:11])
        services = list(ServiceModel.objects.filter().values("id", "title"))
        testmonial_form = TestimonialForm()

        context = {
            "testimonials": testmonials[:10],
            "services": services,
            "testimonial_form": testmonial_form
        }

        if len(testmonials) == 11:
            context["has_more"] = True
            context["next_batch_point"] = testmonials[-1].id



    context["content_tab"] = tab
    context["current"] = "contents"
    context["page_blurb"] = "Manage all the contents displayed across your website."

    return render(request, "dashboard/contents.html", context)



def get_testimonials_next_batch(*args, **kwargs):
    batch_point = kwargs.get("batch_point")
    
    context = get_items_batch(
        query=TestimonialModel.objects.filter(id__lte=batch_point).select_related("service").order_by("-id"),
        size=6,
        tmp="dashboard/partials/contents/_testimonials_list.html",
        name="testimonials",
        point_field="id"
    )

    return JsonResponse(context)
    



def get_faqs_next_batch(*args, **kwargs):
    batch_point = kwargs.get("batch_point")
 
    context = get_items_batch(
        query=FAQsModel.objects.select_related("service").filter(id__lte=batch_point).order_by("-id"),
        size=6,
        tmp="dashboard/partials/contents/_faqs_list.html",
        name="faqs",
        point_field="id"
    )

    return JsonResponse(context)
    



@login_required
@permission_required(("staffs.manage_contents", "staffs.manage_hero",), raise_exception=True)
def update_hero_view(request, type):
    hero_instance = HeroSectionModel.objects.first()
    hero_form = HeroInfoForm(request.POST or None, instance=hero_instance) if type == "info" else HeroImgForm(request.POST or None, request.FILES or None, instance=hero_instance)

    if type == "reset":
        hero_instance.img = ""
        hero_instance.save(update_fields=("img",))

        log_staff_action(staff=request.user, code="content.hero.reset", label="Reset the hero section image.", is_success=True)
        return redirect("dashboard_contents")
    elif hero_form and request.POST and hero_form.is_valid():
        hero_form.save()

        log_staff_action(staff=request.user, code="content.hero.update", label=f"Updated the hero section {type}.", is_success=True)
        return toast_json_ok("Hero updated successfully.")
    
    if request.POST:
        log_staff_action(staff=request.user, code="content.hero.update", label=f"Failed to update hero section {type}.", is_success=False, failure_reason="Invalid form data.")
    return toast_json_error("Can't update hero.", form_errors=hero_form.errors.as_json())



@login_required
@permission_required(("staffs.manage_contents",), raise_exception=True)
def update_about_view(request):
    about_instance = AboutSectionModel.objects.first()
    about_form = AboutForm(request.POST or None, instance=about_instance)

    if request.POST and about_form.is_valid():
        about_form.save()

        log_staff_action(staff=request.user, code="content.about.update", label="Updated the about section information.", is_success=True)
        return toast_json_ok(f"About info has been updated successfully.")
            
    if request.POST:
        log_staff_action(staff=request.user, code="content.about.update", label="Failed to update about section.", is_success=False, failure_reason="Invalid form data.")
    return toast_json_error(f"Can't update about info.", form_errors=about_form.errors.as_json())


@login_required
@permission_required(("staffs.manage_contents", "staffs.manage_team", "staffs.update_team_member"), raise_exception=True)
def update_team_member_view(request, member):
    team_member = TeamModel.objects.filter(slug=member).first()
    team_form = TeamForm(request.POST or None, request.FILES or None, instance=team_member)

    if request.POST and team_form.is_valid():
        team_form.save()
        log_staff_action(staff=request.user, code="team.member.update", label=f"Updated details for team member: {team_member.name}.", is_success=True)
        return toast_json_ok(f"{team_member.name} has been updated successfully.")
    
    if request.POST:
        log_staff_action(staff=request.user, code="team.member.update", label="Failed to update team member.", is_success=False, failure_reason="Invalid form data.")
    return toast_json_error(f"Can't update team member.", form_errors=team_form.errors.as_json())
    

@login_required
@permission_required(("staffs.manage_contents", "staffs.manage_team", "staffs.remove_team_member"), raise_exception=True)
def remove_team_member_view(request, member):
    team_member = TeamModel.objects.filter(slug=member).first()

    if team_member:
        team_member.remove_as_member()
        log_staff_action(staff=request.user, code="team.member.remove", label=f"Removed {team_member.name} as a team member.", is_success=True)
        return toast_json_ok(f"{team_member.name} has been removed successfully.")
    
    log_staff_action(staff=request.user, code="team.member.remove", label="Failed to remove team member.", is_success=False, failure_reason=f"Team member does not exist ({member}).")            
    return toast_json_error(f"Can't remove {member}. Please try again later.")



@login_required
@permission_required(("staffs.manage_contents", "staffs.manage_team", "staffs.add_team_member"), raise_exception=True)
def add_team_member_view(request):
    team_form = TeamForm(request.POST or None, request.FILES or None)

    if request.POST and team_form.is_valid():
        team_form.save()
        log_staff_action(staff=request.user, code="team.member.add", label=f"Added a new team member: {team_form.instance.name}.", is_success=True)
        return toast_json_ok(f"Team member has been added successfully.")
            
    if request.POST:
        log_staff_action(staff=request.user, code="team.member.add", label="Failed to add team member.", is_success=False, failure_reason="Invalid form data.")
    return toast_json_error(f"Can't add team member.", form_errors=team_form.errors.as_json())




@login_required
@permission_required(("staffs.manage_contents", "staffs.manage_services", "staffs.update_service"), raise_exception=True)
def update_service_view(request, service):
    service_inst = ServiceModel.objects.filter(slug=service).first()
    service_form = ServiceForm(request.POST or None, request.FILES or None, instance=service_inst)

    if request.POST and service_form.is_valid():
        service_form.save()

        print(service_form.cleaned_data)

        log_staff_action(staff=request.user, code="service.update", label=f"Updated the service: {service_inst.title}.", is_success=True)
        return toast_json_ok(f"{service_inst.title} was updated successfully.")
    
    if request.POST:
        log_staff_action(staff=request.user, code="service.update", label="Failed to update service.", is_success=False, failure_reason="Invalid form data.")
    return toast_json_error(f"can't update service", form_errors=service_form.errors.as_json())




@login_required
@permission_required(("staffs.manage_contents", "staffs.manage_services", "staffs.delete_service"), raise_exception=True)
def delete_service_view(request, service):
    service_inst = ServiceModel.objects.filter(slug=service).first()

    if service_inst:
        service_inst.delete()

        log_staff_action(staff=request.user, code="service.delete", label=f"Deleted the service: {service_inst.title}.", is_success=True)
        return toast_json_ok(f"{service_inst.title} has been deleted successfully.")
    
    log_staff_action(staff=request.user, code="service.delete", label="Failed to delete service.", is_success=False, failure_reason=f"Service does not exist ({service}).")
    return toast_json_error("Can't delete service. Try again later.")



@login_required
@permission_required(("staffs.manage_contents", "staffs.manage_services", "staffs.add_service"), raise_exception=True)
def add_service_view(request):
    service_form = ServiceForm(request.POST or None, request.FILES or None)

    if request.POST and service_form.is_valid():
        service_form.save()

        print(service_form.cleaned_data)
        log_staff_action(staff=request.user, code="service.add", label=f"Added a new service: {service_form.instance.title}.", is_success=True)
        return toast_json_ok("Service added successfully.")
    
    if request.POST:
        log_staff_action(staff=request.user, code="service.add", label="Failed to add service.", is_success=False, failure_reason="Invalid form data.")
    return toast_json_error("Can't add service", form_errors=service_form.errors.as_json())




@login_required
@permission_required(("staffs.manage_contents", "staffs.manage_faqs", "staffs.update_faq"), raise_exception=True)
def update_faq_view(request, faq):
    faq_inst = FAQsModel.objects.filter(slug=faq).first()
    faqs_form = FAQForm(request.POST or None, instance=faq_inst)

    if request.POST and faqs_form.is_valid() and faq_inst:
        faqs_form.save()

        log_staff_action(staff=request.user, code="faq.update", label=f"Updated FAQ: {faq_inst.question}.", is_success=True)
        return toast_json_ok(f"{faq_inst.question} has been updated successfully.")
    
    if request.POST:
        log_staff_action(staff=request.user, code="faq.update", label="Failed to update FAQ.", is_success=False, failure_reason="Invalid form data or FAQ does not exist.")
    return toast_json_error(f"Can't update FAQ", faqs_form.errors.as_json())
    


@login_required
@permission_required(("staffs.manage_contents", "staffs.manage_faqs", "staffs.delete_faq"), raise_exception=True)
def delete_faq_view(request, faq):
    faq_inst = FAQsModel.objects.filter(slug=faq).first()

    if faq_inst:
        faq_inst.delete()
        log_staff_action(staff=request.user, code="faq.delete", label=f"Deleted FAQ: {faq_inst.question}.", is_success=True)
        return toast_json_ok(f"{faq_inst.question} has been deleted successfully.")
            
    log_staff_action(staff=request.user, code="faq.delete", label="Failed to delete FAQ.", is_success=False, failure_reason=f"FAQ does not exist ({faq}).")
    return toast_json_error(f"Can't delete FAQ. Try again later.")


@login_required
@permission_required(("staffs.manage_contents", "staffs.manage_faqs", "staffs.add_faq"), raise_exception=True)
def add_faq_view(request):
    faq_form = FAQForm(request.POST or None)

    if request.POST and faq_form.is_valid():
        faq_form.save()
        log_staff_action(staff=request.user, code="faq.add", label=f"Added a new FAQ: {faq_form.instance.question}.", is_success=True)
        return toast_json_ok("FAQ added successfully.")

    if request.POST:
        log_staff_action(staff=request.user, code="faq.add", label="Failed to add FAQ.", is_success=False, failure_reason="Invalid form data.")
    return toast_json_error("Can't add FAQ.", form_errors=faq_form.errors.as_json())





@login_required
@permission_required(("staffs.manage_contents", "staffs.manage_testimonials", "staffs.update_testimonial"), raise_exception=True)
def update_testimonial_view(request, testimonial):
    testimonial_inst = TestimonialModel.objects.filter(slug=testimonial).first()
    testimonial_form = TestimonialForm(request.POST or None, instance=testimonial_inst)

    is_not_approved = not testimonial_inst.is_approved

    if request.POST and testimonial_form.is_valid():
        testimonial_form.save()

        if is_not_approved and "is_approved" in testimonial_form.changed_data:
            log_staff_action(staff=request.user, code="testimonial.approve", label=f"Approved testimonial from {testimonial_inst.name}.", is_success=True)
            testimonial_inst.set_approved(staff=request.user)
            return toast_json_ok("Testimonial approved successfully.")

        log_staff_action(staff=request.user, code="testimonial.update", label=f"Updated testimonial from {testimonial_inst.name}.", is_success=True)
        return toast_json_ok("Testimonial updated successfully.")
    
    if request.POST:
        log_staff_action(staff=request.user, code="testimonial.update", label="Failed to update testimonial.", is_success=False, failure_reason="Invalid form data.")
    return toast_json_error("Can't update testimonial.", form_errors=testimonial_form.errors.as_json())


@login_required
@permission_required(("staffs.manage_contents", "staffs.manage_testimonials", "staffs.add_testimonial"), raise_exception=True)
def add_testimonial_view(request):
    testimonial_form = TestimonialForm(request.POST or None)

    if request.POST and testimonial_form.is_valid():
        testimonial_form.save()

        log_staff_action(staff=request.user, code="testimonial.add", label=f"Added a new testimonial for {testimonial_form.instance.name}.", is_success=True)
        return toast_json_ok("Testimonial added successfully.")
    
    if request.POST:
        log_staff_action(staff=request.user, code="testimonial.add", label="Failed to add testimonial.", is_success=False, failure_reason="Invalid form data.")
    return toast_json_error("Can't add testimonial.", form_errors=testimonial_form.errors.as_json())



@login_required
@permission_required(("staffs.manage_contents", "staffs.manage_testimonials", "staffs.update_testimonial"), raise_exception=True)
def delete_testimonial_view(request, testimonial):
    testimonial_inst = TestimonialModel.objects.filter(slug=testimonial).first()
    
    if testimonial_inst:
        testimonial_inst.delete()

        log_staff_action(staff=request.user, code="testimonial.delete", label=f"Deleted testimonial from {testimonial_inst.name}.", is_success=True)
        return toast_json_ok("Testimonial deleted successfully.")
    
    log_staff_action(staff=request.user, code="testimonial.delete", label="Failed to delete testimonial.", is_success=False, failure_reason=f"Testimonial does not exist ({testimonial}).")
    return toast_json_error("Can't delete testimonial. Try again later.")





@login_required
@permission_required(("staffs.manage_messages"), raise_exception=True)
def communication_view(request):
    contact_messages = list(ContactMessageModel.objects.filter().order_by("-id")[:11])
    has_more = len(contact_messages) == 11
    
    context = {
        "contact_messages": contact_messages[:10],
        "messages_batch_point": contact_messages[-1].id if has_more else None,
        "more_messages": True if has_more else None,
        "current": "communication"
    }

    return render(request, "dashboard/communication.html", context)



@login_required
@permission_required(("staffs.manage_messages", "staffs.view_messages"), raise_exception=True)
def get_messages_batch_view(request, batch_point):
    context = get_items_batch(
        query=ContactMessageModel.objects.filter(id__lte=batch_point).order_by("-id"),
        size=6,
        tmp="dashboard/partials/communication/_rows.html",
        name="contact_messages",
        point_field="id"
    )

    return JsonResponse(context)




@login_required
@permission_required(("staffs.manage_messages", "staffs.reply_message",), raise_exception=True)
def attend_message_view(request, message):
    message_inst = ContactMessageModel.objects.filter(id=message).first()

    if message_inst:
        if message_inst.is_attended:
            log_staff_action(staff=request.user, code="message.attend", label="Failed to attend contact message.", is_success=False, failure_reason=f"Message from {message_inst.name} is already attended.")
            return toast_json_error(f"Message from {message_inst.name} has been attended to already.")
        
        if not message_inst.is_attended:
            message_inst.set_attended(request)

            log_staff_action(staff=request.user, code="message.attend", label=f"Attended to contact message from {message_inst.name}.", is_success=True)
            return toast_json_ok(f"Message from {message_inst.name} has been set to be attended by you.")

    log_staff_action(staff=request.user, code="message.attend", label="Failed to attend contact message.", is_success=False, failure_reason=f"Message does not exist (ID: {message}).")
    return toast_json_error("Can't update message status. Try again later.")



@login_required
@permission_required(("staffs.manage_messages", "staffs.reply_message",), raise_exception=True)
def unattend_message_view(request, message):
    message_inst = ContactMessageModel.objects.filter(id=message).first()

    if message_inst:
        if not message_inst.is_attended:
            log_staff_action(staff=request.user, code="message.unattend", label="Failed to unattend message.", is_success=False, failure_reason="Message was never attended.")
            return toast_json_error("Can't update message status, message is yet to be attended to.")

        if not message_inst.attended_by == request.user:
            log_staff_action(staff=request.user, code="message.unattend", label="Failed to unattend message.", is_success=False, failure_reason="Message was attended by a different staff member.")
            return toast_json_error("Can't update message status, message was attended to by another staff.")

        if message_inst.attended_by == request.user:
            message_inst.set_unattended()

            log_staff_action(staff=request.user, code="message.unattend", label=f"Unattended contact message from {message_inst.name}.", is_success=True)
            return toast_json_ok(f"Message from {message_inst.name} hase been set to not attended successfully.")

    log_staff_action(staff=request.user, code="message.unattend", label="Failed to unattend message.", is_success=False, failure_reason=f"Message does not exist (ID: {message}).")
    return toast_json_error("Can't update message status.")




@login_required
@permission_required(("staffs.manage_messages", "staffs.delete_message"), raise_exception=True)
def delete_message_view(request, message):
    message_inst = ContactMessageModel.objects.filter(id=message).first()

    if message_inst:
        message_inst.delete()

        log_staff_action(staff=request.user, code="message.delete", label=f"Deleted contact message from {message_inst.name}.", is_success=True)
        return toast_json_ok(f"Message from {message_inst.name} has been deleted successfullt.")
    
    log_staff_action(staff=request.user, code="message.delete", label="Failed to delete message.", is_success=False, failure_reason=f"Message does not exist (ID: {message}).")
    return toast_json_error("Can't delete message. Try agan later.")



@login_required
@permission_required(("staffs.manage_staffs",), raise_exception=True)
def staffs_view(request):
    staffs = CustomUserModel.objects.select_related("profile",).filter()
    change_email_form = ChangeEmailForm(request.POST or None)
    staff_form = StaffForm(request.POST or None)

    context = {
        "staffs": staffs,
        "change_email_form": change_email_form,
        "staff_form": staff_form,
        "current": "staffs"
    }

    return render(request, "dashboard/staffs.html", context)






@login_required
@permission_required(("staffs.manage_staffs", "staffs.add_user"), raise_exception=True)
def add_staff_view(request):
    staff_form = StaffForm(request.POST or None)

    if request.POST and staff_form.is_valid():
        data = staff_form.cleaned_data
        name = f"{data['first_name']} {data['last_name']}"
        email = data["email"]   

        if check_staff_email(email=email):
            log_staff_action(staff=request.user, code="staff.invite", label="Failed to invite staff member.", is_success=False, failure_reason=f"Email already exists ({email}).")
            return toast_json_error("Can't add staff.", error="Staff already exists")

        invalidate_add_staff_tracks(email=email) # invalidate exisiting tracks and void existing tokens
        
        staff_form.save()

        try:
            add_new_staff(email=email, name=name, action_source="dashboard", initiator=request.user)
        except Exception as e:
            log_staff_action(staff=request.user, code="staff.invite", label=f"Can't initiate account creation for new staff: {email}.", is_success=False, failure_reason=e)
            return toast_json_error("Account creation not initiated. Try again later.")

        log_staff_action(staff=request.user, code="staff.invite", label=f"Initiated account creation for new staff: {email}.", is_success=True)
        
        return toast_json_ok("Staff added successfully.")

    if request.POST:
        log_staff_action(staff=request.user, code="staff.invite", label="Failed to send staff invitation.", is_success=False, failure_reason="Invalid form data.")

    
    return toast_json_error("Account creation not initiated", form_errors=staff_form.errors.as_json())



@login_required
@permission_required(("staffs.view_reports",), raise_exception=True)
def reports_view(request):
    (range_to, range_from, range_prior), (range_space, from_date, to_date) = get_reports_range(request)

    all_enquiries = ContactMessageModel.objects.filter()
    enquiries = all_enquiries.filter(created_at__range=(range_from, range_to))

    counts = get_enquiries_counts(all_enquiries=all_enquiries, range_from=range_from, range_to=range_to, range_prior=range_prior)
    enquiries_count, prior_enquiries_count, unattended_enquirires_count, unattended_enquirires_over_24h_count = tuple(counts.values())
    enquiries_change_percent = get_change_percent(prior=prior_enquiries_count, current=enquiries_count)

    avg_response_seconds, prior_avg_response_seconds = get_average_response_time(all_enquiries=all_enquiries, range_from=range_from, range_to=range_to, range_prior=range_prior)
    avg_response_change_percent = get_change_percent(prior=prior_avg_response_seconds, current=avg_response_seconds)

    oldest_unattended = enquiries.filter(is_attended=False).order_by("created_at").first()
    oldest_unattended_enquirires_days = oldest_unattended.get_days_from_now() if oldest_unattended else None
    
    pending_testimonials = TestimonialModel.objects.filter(created_at__range=(range_from, range_to), is_approved=False)
    pending_testimonials_count = pending_testimonials.count()
    oldest_pending_testimonials_days = pending_testimonials.order_by("created_at").first().get_days_from_now() if pending_testimonials_count else None
    

    enquiries_series = get_enquiries_series(enquiries=enquiries)
    enquiries_by_service = get_enquiries_by_services(range_from=range_from, range_to=range_to, enquiries_count=enquiries_count)

    responce_performance = get_response_performance(unattended_enquirires_over_24h_count)

    by_weekday, peak = get_busiest_days(enquiries=enquiries)
    
    health = get_content_health(pending_testimonials=pending_testimonials)



    summary = {
        "enquiries": enquiries_count,
        "enquiries_change": enquiries_change_percent,
        "unattended": unattended_enquirires_count,
        "oldest_unattended_days": oldest_unattended_enquirires_days,
        "avg_response_seconds": avg_response_seconds,
        "avg_response_change": avg_response_change_percent,
        "pending_testimonials": pending_testimonials_count,
        "oldest_pending_days": oldest_pending_testimonials_days
    }


    context = {
        "range": range_space, # 7d, 30d, 90d or custom
        "from": from_date,
        "to": to_date,
        "summary": summary,
        "enquiries_series": enquiries_series,
        "by_service": enquiries_by_service,
        "response_perf": responce_performance,
        "by_weekday": by_weekday,
        "peak": peak,
        "health": health,
        "current": "reports"
    }


    return render(request, "dashboard/reports.html", context)




@login_required
@permission_required(("staffs.view_reports",), raise_exception=True)
def get_site_analytics_view(request):
    (range_to, range_from, _), (range_space, from_date, to_date) = get_reports_range(request)

    date = {
        "7d": timezone.now() - timedelta(days=7),
        "30d": timezone.now() - timedelta(days=30),
        "90d": timezone.now() - timedelta(days=90)
    }
    
    range_info = {
        "from_date": from_date if range_space == "custom" else date[range_space],
        "to_date": to_date if range_space == "custom" else timezone.now()
    }

    
    public_site_analytics_data = get_umami_analytics_data(id=os.getenv("UMAMI_PUBLIC_WEBSITE_ID"), start_datetime=range_from, end_datetime=range_to)

    analytics = {
        "public_site_analytics_data": public_site_analytics_data,
        "range_info": range_info
    }


    return JsonResponse(analytics)





@login_required
@permission_required(("staffs.view_reports", "staffs.view_staffs_action_logs"), raise_exception=True)
def get_staff_actions_logs_view(request, staff_email):
    staff = CustomUserModel.objects.select_related("profile").filter(email=staff_email).first()
   
    if not staff:
        return JsonResponse({"error": "Staff not found"}, status=404)

    
    logs = get_staff_actions_logs(request=request, staff=staff)

    return JsonResponse(logs, status=200)




@login_required
@permission_required(("staffs.view_reports", "staffs.view_staffs_action_logs"), raise_exception=True)
def get_staff_recent_actions_batch_view(request, staff_email, batch_point):
    staff = CustomUserModel.objects.select_related("profile").filter(email=staff_email).first()
       
    if not staff:
        return JsonResponse({"error": "Staff not found"}, status=404)

    recent_actions = get_recent_staff_actions(staff=staff, batch_point=batch_point)
    

    return JsonResponse(recent_actions, status=200)

    