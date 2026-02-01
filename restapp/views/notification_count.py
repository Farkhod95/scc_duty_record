# views.py
from typing import Set

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status as drf_status

from restapp.models import Notification

def _role_names(user) -> Set[str]:
    if not getattr(user, "is_authenticated", False):
        return set()
    return {str(name).strip().lower() for name in user.roles.values_list("name", flat=True)}


class NotificationCountView(APIView):

    def get(self, request):
        status_param = (request.GET.get("status") or "").strip().lower()
        responsible_by_param = (request.GET.get("responsible_by") or "").strip()

        # status validate
        allowed_statuses = {k.lower() for k, _ in Notification.STATUS.choices}
        if not status_param:
            return Response(
                {"detail": "status param majburiy. (unread/read)"},
                status=drf_status.HTTP_400_BAD_REQUEST,
            )
        if status_param not in allowed_statuses:
            return Response(
                {"detail": f"status noto'g'ri. Ruxsat: {sorted(list(allowed_statuses))}"},
                status=drf_status.HTTP_400_BAD_REQUEST,
            )

        # role check
        roles = _role_names(request.user)
        is_admin_like = ("super admin" in roles) or ("admin" in roles)

        qs = Notification.objects.filter(status=status_param)

        # if not is_admin_like:
        #     # non-admin -> responsible_by majburiy
        if not responsible_by_param:
            return Response(
                {"detail": "responsible_by param majburiy (admin/super admin bo'lmaganlar uchun)."},
                status=drf_status.HTTP_400_BAD_REQUEST,
            )
        try:
            responsible_by_id = int(responsible_by_param)
        except ValueError:
            return Response(
                {"detail": "responsible_by butun son bo'lishi kerak."},
                status=drf_status.HTTP_400_BAD_REQUEST,
            )

        qs = qs.filter(responsible_by_id=responsible_by_id)
        # else:
        #     responsible_by_id = None  # adminlar uchun ko'rsatilmaydi

        return Response(
            {
                "status": status_param,
                "responsible_by": responsible_by_id,
                "count": qs.count(),
                # "is_admin_like": is_admin_like,
                # "roles": sorted(list(roles)),
            },
            status=drf_status.HTTP_200_OK,
        )
