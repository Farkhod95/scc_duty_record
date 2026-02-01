# restapp/utils.py
from typing import Any

from django.http import HttpRequest

from restapp.models import ModelChangeLog
from users.models import User  # ⚠️ kerakli joy bo'yicha import qil

def get_client_ip(request: HttpRequest) -> str | None:
    """
    X-Forwarded-For bo'lsa undan, bo'lmasa REMOTE_ADDR dan IP olamiz.
    """
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0].strip()
    else:
        ip = request.META.get("REMOTE_ADDR", None)
    return ip


def log_model_view(
    request: HttpRequest,
    *,
    app_label: str,
    model_name: str,
    object_id: str | int,
    extra: dict | None = None,
):
    """
    GET / VIEW actionlar uchun umumiy logger.

    target_obj:
      - agar User bo'lsa, ko‘rilgan user haqida:
        id, username, FIO, pinfl, passport_series, passport_number
        ma'lumotlar ham yozib qo‘yiladi.
    """
    user = request.user if getattr(request, "user", None) and request.user.is_authenticated else None
    ip = get_client_ip(request)
    ua = request.META.get("HTTP_USER_AGENT", "")

    meta: dict[str, Any] = {
        "event": "view",
        "path": request.path,
        "method": request.method,
        # "query_params": query,
        "ip_address": ip,
        "user_agent": ua[:500],
    }

    if extra:
        meta.update({"description": extra})

    ModelChangeLog.objects.create(
        app_label=app_label,
        model_name=model_name,
        object_id=str(object_id),
        action=ModelChangeLog.ActionChoices.VIEW,
        user=user,
        data_before=None,
        data_after=meta,
    )
