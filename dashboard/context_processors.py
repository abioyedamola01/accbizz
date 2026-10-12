from django.contrib.auth.decorators import login_required
from dashboard.models import ContactMessageModel



def contact_messages_count(request):
    if request.user.is_authenticated:
        messages_count = ContactMessageModel.objects.count()
        unattended_count = ContactMessageModel.objects.filter(is_attended=False).count()

        context = {
            "total_count": messages_count,
            "unattended_count": unattended_count
        }

        return context
    return {}