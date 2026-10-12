from dashboard.models import (SiteModel, ServiceModel,)

def footer_info(request):
    site_info = SiteModel.objects.filter().first()
    services = ServiceModel.objects.filter().order_by("?")[:5]

    context = {
        "site_info": site_info,
        "footer_services": services
    }

    return context