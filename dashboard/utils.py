from django.http import JsonResponse

def toast_json_ok(message, status=200, *args, **kwargs):
    load = {
        "ok": True,
        "message": message
    }

    if "url" in kwargs.keys():
        load["url"] = kwargs["url"]

    return JsonResponse(load, status=status)

def toast_json_error(message, errors=None, status=400):
    load = {
        "ok": False,
        "message": message
    }

    if errors:
        load["errors"] = errors

    return JsonResponse(load, status=status)



