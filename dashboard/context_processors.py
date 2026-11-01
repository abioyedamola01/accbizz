from django.db.models import (Count, Q,)
from dashboard.models import (ContactMessageModel, TestimonialModel, FAQsModel,)



def contact_messages_count(request):
    context = {}
    if request.user.is_authenticated and request.user.has_perm("staffs.view_messages"):
        context = ContactMessageModel.objects.aggregate(
            messages_count=Count("id"),
            unattended_count=Count("id", filter=Q(is_attended=False))
        )

    return context


def testimonials_count(request):
    context = {}
    if request.user.is_authenticated and request.user.has_perm("staffs.manage_testimonials"):
        context = TestimonialModel.objects.aggregate(
            testimonials_count=Count("id"),
            unapproved_count=Count("id", filter=Q(is_approved=False))
        )

    return context



def faqs_count(request):
    context = {}
    if request.user.is_authenticated and request.user.has_perm("staffs.manage_faqs"):
        context = TestimonialModel.objects.aggregate(
            faqs_count=Count("id")
        )

    return context