import os
import requests
from datetime import (timedelta, datetime,)
from django.http import JsonResponse
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.postgres.aggregates import ArrayAgg
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.urls import reverse
from django.db.models import (Count, Avg, Subquery, Value, Q, F)
from django.db.models.functions import (TruncDate, TruncHour, TruncDay, Concat, Length,)
from staffs.models import (CustomUserModel, StaffActionsLogModel,)
from .models import (ServiceModel, SiteModel, AddStaffModel,)


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






def get_reports_range(request):
    rs = str(request.GET.get("range", "30d")).lower()

    range_space = rs if rs in ("7d", "30", "90d", "custom") else "30d"
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





def log_staff_action(**args):
    StaffActionsLogModel.objects.create(**args)


def get_logs_series(logs):
    points = list(logs.annotate(date=TruncDay("created_at")).values("date").annotate(count=Count("id"), failed=Count("id", filter=Q(is_success=False))).order_by("date"))

    return {"points": points}


def get_logs_by_action(logs):
    by_codes = list(logs.values("code").annotate(count=Count("id"), failed=Count("id", filter=Q(is_success=False))).order_by("code"))
    
    return by_codes
    

def get_failures_by_reason(logs, reasons):
    by_reason = list(logs.annotate(reason=F("failure_reason")).values("reason").annotate(count=Count("id")).order_by("failure_reason"))

    return by_reason


def get_recent_staff_actions(staff, batch_point):
    recent_actions = get_items_batch(
        query=StaffActionsLogModel.objects.order_by("-created_at").filter(staff=staff, created_at__lte=batch_point),
        size=6,
        tmp="dashboard/partials/staffs/_recent_actions.html",
        name="actions",
        point_field="created_at",
    )
    
    return recent_actions






def get_staff_actions_logs(request, staff):
    (range_to, range_from, _), (range_space, _, _) = get_reports_range(request=request)


    actions_logs = StaffActionsLogModel.objects.order_by("-created_at").filter(staff=staff, created_at__range=(range_from, range_to))
    actions_count = actions_logs.count()

    failed_actions_logs = actions_logs.filter(is_success=False)
    failed_actions_count = failed_actions_logs.count()
    
    last_action = actions_logs.first()

    logs_series = get_logs_series(logs=actions_logs)
        
    by_action = get_logs_by_action(logs=actions_logs)
    
    failure_reasons = set(failed_actions_logs.values_list("failure_reason", flat=True))
    by_reason = get_failures_by_reason(logs=failed_actions_logs, reasons=failure_reasons)

    recent_actions = get_recent_staff_actions(staff=staff, batch_point=timezone.now())
    

    range_info = {
        "range": range_space,
        "range_from": range_from,
        "range_to": range_to
    }

    staff_info = {
        "name": staff.profile.username,
        "email": staff.email,
        "role": staff.profile.role,
        "status": "Active" if staff.is_staff_member else "Not Active",
        "last_login": staff.last_login
    }

    summary = {
        "total_actions": actions_count,
        "failed_actions": failed_actions_count,
        "last_action_at": last_action.created_at,
        "last_action_label": last_action.label
    }

    logs = {
        "range_info": range_info,
        "staff": staff_info,
        "summary": summary,
        "series": logs_series,
        "by_action": by_action,
        "failures_by_reason": by_reason,
        "recent_actions": recent_actions
    }

    return logs





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

def get_enquiries_counts(all_enquiries, range_from, range_to, range_prior):
    day = range_to - timedelta(days=1)

    counts = all_enquiries.aggregate(
        enquiries_count=Count("id", filter=Q(created_at__range=(range_from, range_to))),
        prior_enquiries_count=Count("id", filter=Q(created_at__range=(range_prior, range_from))),
        unattended_enquirires_count=Count("id", filter=Q(created_at__range=(range_from, range_to), is_attended=False)),
        unattended_enquirires_over_24h_count=Count("id", filter=Q(created_at__range=(range_from, day)), is_attended=False)
    )


    return counts



def get_average_response_time(all_enquiries, range_from, range_to, range_prior):
    response_average = all_enquiries.filter(is_attended=True).annotate(response_time=F("attended_at") - F("created_at")).aggregate(
        avg_response_seconds=Avg("response_time", filter=Q(created_at__range=(range_from, range_to))),
        prior_avg_response_seconds=Avg("response_time", filter=Q(created_at__range=(range_prior, range_from)))
    )

    avg_response_seconds = response_average["avg_response_seconds"].seconds if response_average["avg_response_seconds"] else 0
    prior_avg_response_seconds = response_average["prior_avg_response_seconds"].seconds if response_average["prior_avg_response_seconds"] else 0

    return (avg_response_seconds, prior_avg_response_seconds)





def get_change_percent(prior, current):
    percent = ((current - prior) / prior) * 100 if prior else 0
    return percent



def get_enquiries_series(enquiries):
    series = list(enquiries.annotate(date=TruncDay("created_at")).values("date").annotate(count=Count("id")).order_by("date"))

    return series



def get_enquiries_by_services(range_from, range_to, enquiries_count):
    services = ServiceModel.objects.filter(is_active=True, enquiries__created_at__range=(range_from, range_to))

    by_services = list(services.annotate(count=Count("enquiries")).values("title", "count"))
    
    services_enquiries_count = sum(dic["count"] for dic in by_services)

    gen_count = enquiries_count - services_enquiries_count

    if gen_count: by_services.append({"title": "General Enquiry", "count": gen_count})


    return by_services


def get_response_performance(unattended_enquirires_over_24h_count):
    staffs = CustomUserModel.objects.select_related("profile").filter()

    by_staffs = list(staffs.annotate(name=Concat("profile__first_name", Value(" "), "profile__last_name"), attended=Count("attended_enquiries")).values("name", "email", "attended"))

    response_performance = {
        "attended_by_staff": by_staffs,
        "unattended_over_24h": unattended_enquirires_over_24h_count
    }
    
    return response_performance





def get_keys_from_value(value, dic):
    keys = [key for key, val  in dic.items() if val == value]
    return keys

def get_busiest_days(enquiries):
    by_weekday = enquiries.aggregate(
        Sun=Count("id", filter=Q(created_at__week_day=1)),
        Mon=Count("id", filter=Q(created_at__week_day=2)),
        Tue=Count("id", filter=Q(created_at__week_day=3)),
        Wed=Count("id", filter=Q(created_at__week_day=4)),
        Thu=Count("id", filter=Q(created_at__week_day=5)),
        Fri=Count("id", filter=Q(created_at__week_day=6)),
        Sat=Count("id", filter=Q(created_at__week_day=7)),
    )

    counts = by_weekday.values()

    max_count = max(counts)
    max_count_days = get_keys_from_value(value=max_count, dic=by_weekday)
    min_count_days = get_keys_from_value(value=min(counts), dic=by_weekday)


    peak = {
        "busiest_days": max_count_days,
        "busiest_days_count": max_count,
        "quietest_days": min_count_days
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
    contents = SiteModel.objects.values("company_name", "display_name", "tagline", "email", "whatsapp", "location", "logo", "favicon")[0]
    setup_fields = [{"label": key, "ok": bool(val)} for key, val in contents.items()]

    counts = ServiceModel.objects.filter(is_active=True).aggregate(
        no_faqs_count=Count("id", filter=Q(faqs__isnull=True)),
        no_testimonials_count=Count("id", filter=Q(testimonials__isnull=True))
    )
    no_faqs_count, no_testimonials_count = counts.values()

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







def get_items_batch(query, size, tmp, name, point_field):
    trunc_size = size if point_field == "created_at" else size + 1
    objects = list(query[:trunc_size])

    context = {}

    if objects:
        has_more = len(objects) == int(trunc_size)
        html = render_to_string(f"{tmp}", {f"{name}": objects[:size]})

        context = {
            "html": html,
            "has_more": has_more
        }

        if point_field == "created_at":
            context["next_batch_point"] = objects[-1].created_at if has_more else None
        else:
            context["next_batch_point"] = objects[-1].id if has_more else None


    return context