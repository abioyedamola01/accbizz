from django import template

register = template.Library()


@register.filter
def short_duration(seconds):
    """3 hours 20 minutes -> "3h 20m". Handles None and bad values with a dash."""
    try:
        total = int(seconds)
    except (TypeError, ValueError):
        return "\u2014"
    if total < 0:
        return "\u2014"

    days, rest = divmod(total, 86400)
    hours, rest = divmod(rest, 3600)
    minutes = rest // 60

    if days:
        return f"{days}d {hours}h" if hours else f"{days}d"
    if hours:
        return f"{hours}h {minutes}m" if minutes else f"{hours}h"
    if minutes:
        return f"{minutes}m"
    return "<1m"