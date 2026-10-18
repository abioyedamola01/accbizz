from django import template

register = template.Library()


@register.filter
def mask_email(value):
    if not value:
        return ""

    value = str(value)
    local, at, domain = value.rpartition("@")

    # Not a normal email (no "@"): hide everything
    if not at:
        return "****"

    visible = local[:3] if len(local) > 3 else ""
    return f"{visible}****@{domain}"