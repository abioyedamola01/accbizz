from django.http import JsonResponse

def toast_json_ok(message, status=200, *args, **kwargs):
    load = {
        "ok": True,
        "message": message
    }

    for key, value in kwargs.items():
        load[str(key)] = value

    return JsonResponse(load, status=status)

def toast_json_error(message, errors=None, status=400):
    load = {
        "ok": False,
        "message": message
    }

    if errors:
        load["errors"] = errors

    return JsonResponse(load, status=status)



