import os
import requests
from datetime import (timedelta, datetime,)
from django.http import JsonResponse
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.urls import reverse
from .models import AddStaffModel
from staffs.models import CustomUserModel
from .models import (ServiceModel, SiteModel, TestimonialModel,)


def toast_json_ok(message, status=200, *args, **kwargs):
    load = {
        "ok": True,
        "message": message
    }

    for key, value in kwargs.items():
        load[str(key)] = value

    return JsonResponse(load, status=status)

def toast_json_error(message, status=400, *args, **kwargs):
    load = {
        "ok": False,
        "message": message
    }

    for key, value in kwargs.items():
        load[str(key)] = value

    return JsonResponse(load, status=status)





class AddStaffTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, inst, timestamp):
        value = f"{inst.pk}{timestamp}{inst.email}{inst.is_used}{inst.is_valid}"
        return value

add_staff_token_generator = AddStaffTokenGenerator()


def invalidate_add_staff_tracks(email):
    for track in AddStaffModel.objects.filter(email=email, is_valid=True):
        track.invalidate()


def send_account_creation_email(name, email, url):

    context = {
        "name": name,
        "url": url
    }

    html_message = render_to_string("messages/account_creation_message.html", context=context)

    send_mail(
        subject="Finish creating your staff account",
        message=f"Dear {name},\n\nA staff account has been set up for you. To finish creating it, open the link below and create a new password:\n{url}\n\nThis link expires in 24 hours and can only be used once.\n\nIf you did not expect this email, you can ignore it and no account will be created. Never forward this email to anyone, because the link lets whoever has it set the password for your account.\n\nYou are receiving this because a staff account was set up for this email address.\n",
        from_email= None,
        recipient_list=[email],
        html_message=html_message,
        fail_silently=False,
    )









# reports utils

def get_reports_range(request):
    range_space = str(request.GET.get("range", "30d")).lower() if len(request.GET.get("range", "30d")) else "30d"
    from_date = None
    to_date = None

    range_space_dates = {
        # to_date 0, from_date 1, prior_date 2
        "7d": (timezone.now(), timezone.now() - timedelta(days=7), timezone.now() - timedelta(days=14)),
        "30d": (timezone.now(), timezone.now() - timedelta(days=30), timezone.now() - timedelta(days=60)),
        "90d": (timezone.now(), timezone.now() - timedelta(days=90), timezone.now() - timedelta(days=180)),
    }


    if range_space == "custom":
        from_date = datetime.fromisoformat(str(request.GET.get("from", None))).replace(tzinfo=timezone.UTC)
        to_date = datetime.fromisoformat(str(request.GET.get("to", None))).replace(tzinfo=timezone.UTC)
        range_space_dates["custom"] = (to_date, from_date, from_date - to_date + from_date)

    
    return (range_space_dates[range_space], (range_space, from_date, to_date))



def get_average_response_time(attended_enquiries_timespaces):
    time_space_summation = 0
    for attended_at, created_at in attended_enquiries_timespaces:
        time_space_summation += (attended_at - created_at).seconds if attended_at else 0

    return time_space_summation / len(attended_enquiries_timespaces) if time_space_summation else 0


def get_change_percent(prior, current):
    percent = ((current - prior) / prior) * 100 if prior else 0
    return percent


def get_enquiries_series(range_space_dates, enquiries):
    to_date, from_date, _ = range_space_dates
    enquiries_series = list()

    iterator = from_date
    while iterator <= to_date:
        date = iterator.date()
        next_iterator = iterator + timedelta(days=1)
        enquiries_count = enquiries.filter(created_at__range=(iterator, next_iterator)).count()

        iterator = next_iterator
        enquiries_series.append({
            "date": date,
            "count": enquiries_count
        })

    return enquiries_series


def get_enquiries_by_services(enquiries, enquiries_count):
    services = ServiceModel.objects.filter(is_active=True).values("title")

    enquiries_by_services = ["General Enquiry"]
    enquiries_by_services_count = 0
    
    for service in services:
        title = service["title"]
        count = enquiries.filter(service=title).count()

        enquiries_by_services.append({
            "title": title,
            "count": count
        })

        enquiries_by_services_count += count

    general_enquiry_count = enquiries_count - enquiries_by_services_count

    enquiries_by_services[0] = {"title": "General Enquiry", "count":general_enquiry_count}

    return enquiries_by_services


def get_response_performance(attended_enquiries, unattended_enquiries):
    staffs = CustomUserModel.objects.select_related("profile").filter()

    attended_by_staff = list()

    for staff in staffs:
        count = attended_enquiries.filter(attended_by=staff).count()
        attended_by_staff.append({
            "name": staff.email,
            "attended": count
        })

    unattended_enquiries_over_24hrs_count = unattended_enquiries.filter(created_at__lt=timezone.now()-timedelta(days=1)).count()

    response_performance = {
        "attended_by_staff": attended_by_staff,
        "unattended_over_24h": unattended_enquiries_over_24hrs_count
    }

    return response_performance




def get_keys_from_value(value, dic_list):
    keys = [dic["label"] for dic in dic_list for key, val in dic.items() if val == value]
    return keys


def get_busiest_days(enquiries):
    week = [("Sun", 1), ("Mon", 2), ("Tue", 3), ("Wed", 4), ("Thu", 5), ("Fri", 6), ("Sat", 6)]

    by_weekday = list()

    for day, i in week:
        count = enquiries.filter(created_at__week_day=i).count()
        
        by_weekday.append({
            "label": day,
            "count": count
        })

    count_track = list()

    for item in by_weekday: count_track.append(item["count"])

    busiest_count = max(count_track)
    quietest_count = min(count_track)

    busiest_days = get_keys_from_value(busiest_count, by_weekday)
    quietest_days = get_keys_from_value(quietest_count, by_weekday)


    peak = {
        "busiest_days": busiest_days,
        "busiest_days_count": busiest_count,
        "quietest_days": quietest_days
    }

    return by_weekday, peak



def get_milliseconds(iso_date):
    dt = datetime.fromisoformat(str(iso_date))
    ms = int(dt.timestamp() * 1000)

    return ms


def get_umami_analytics_data(id, start_datetime, end_datetime):
    API_URL = os.getenv("UMAMI_API_URL")
    WEBSITE_ID = id
    API_KEY = os.getenv("UMAMI_API_KEY")


    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Accept": "application/json"
    }

    website_endpoint = f"{API_URL}/websites/{WEBSITE_ID}"

    start_ms = get_milliseconds(iso_date=start_datetime)
    end_ms = get_milliseconds(iso_date=end_datetime)

    stats_params = {
        "startAt": start_ms,
        "endAt": end_ms
    }

    page_views_params = {
        "startAt": start_ms,
        "endAt": end_ms,
        "unit": "day",
        "timezone": "Africa/Lagos" 
    }

    events_params = {
        "startAt": start_ms,
        "endAt": end_ms,
        "page": 1,
        "pageSize": 10
    }

    stats_res = requests.get(f"{website_endpoint}/stats", headers=headers, params=stats_params)
    events_res = requests.get(f"{website_endpoint}/events", headers=headers, params=events_params)
    page_views_res = requests.get(f"{website_endpoint}/pageviews", headers=headers, params=page_views_params)

    stats_analytics = {
        "response": stats_res.json() if stats_res.status_code == 200 else {},
        "error": stats_res.text if stats_res.status_code != 200 else None,
        "status_code": stats_res.status_code
    }

    events_analytics = {
        "response": events_res.json() if events_res.status_code == 200 else {},
        "error": events_res.text if events_res.status_code != 200 else None,
        "status_code": events_res.status_code
    }

    page_views_analytics = {
        "response": page_views_res.json() if page_views_res.status_code == 200 else {},
        "error": page_views_res.text if page_views_res.status_code != 200 else None,
        "status_code": page_views_res.status_code
    }

    data_by_metrics = {}
    metrics_config = (
        ("path", 10),
        ("event", 20),
        ("country", 10),
        ("city", 10)
    )

    for metric_type, metric_limit in metrics_config:
        metric_params = {
            "startAt": start_ms,
            "endAt": end_ms,
            "type": metric_type,
            "limit": metric_limit
        }
        
        metric_res = requests.get(f"{website_endpoint}/metrics/expanded", headers=headers, params=metric_params)

        data_by_metrics[metric_type] = {
            "response": metric_res.json() if metric_res.status_code == 200 else {},
            "error": metric_res.text if metric_res.status_code != 200 else None,
            "status_code": metric_res.status_code
        }


    analytics = {
        "stats": stats_analytics,
        "page_views": page_views_analytics,
        "events": events_analytics,
        "data_by_metrics": data_by_metrics
    }

    
    return analytics




def get_content_health(pending_testimonials):
    site_content = SiteModel.objects.values("company_name", "display_name", "tagline", "email", "whatsapp", "location", "logo", "favicon")[0]
    
    setup_fields = list()

    for key, value in site_content.items():
        field = {
            "label": key,
            "ok": True if len(value) else False
        }

        setup_fields.append(field)


    services = ServiceModel.objects.prefetch_related("faqs", "testimonials").filter(is_active=True)
    no_faqs_count = 0
    no_testimonials_count = 0

    for service in services:
        no_faqs_count += 1 if not service.faqs.filter() else no_faqs_count
        no_testimonials_count += 1 if not service.testimonials.filter() else no_testimonials_count


    pending_testimonials_count_over_7d = pending_testimonials.filter(created_at__lt=timezone.now()-timedelta(days=7)).count()

    health = {
        "site_setup": {
            "fields": setup_fields,
            "fix_url": reverse("dashboard_site")
        },
        "gaps": {
            "services_without_faqs": no_faqs_count,
            "services_without_testimonials": no_testimonials_count,
            "pending_testimonials_over_7_days": pending_testimonials_count_over_7d
        }
    }
    

    return health