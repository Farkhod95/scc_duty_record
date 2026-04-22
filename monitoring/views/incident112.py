from django.conf import settings
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView

from monitoring.models import Incident112, Incident112Notification
from monitoring.serializers.incident112 import (
    Incident112CreateSerializer,
    Incident112ListSerializer,
    Incident112DetailSerializer,
    Incident112NotificationSerializer,
)


class ApiKeyPermission(BasePermission):
    """X-Api-Key headerini tekshiradi."""

    def has_permission(self, request, view):
        expected = getattr(settings, 'INCIDENT_112_API_KEY', '')
        if not expected:
            return False
        provided = request.headers.get('X-Api-Key', '')
        return provided == expected


# ── 112 tizimi uchun (API key) ────────────────────────────────────

class Incident112ReceiveView(APIView):
    """
    POST /api/v1/incidents/112/receive/
    Faqat X-Api-Key: <key> bilan kirish mumkin.
    Hodisani saqlaydi va yaqin xodimlarga WebSocket orqali yuboradi.
    """
    permission_classes = [ApiKeyPermission]

    def post(self, request):
        serializer = Incident112CreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        incident, created = serializer.save(raw_payload=request.data)

        # Celery task: yaqin xodimlarni topib WebSocket yuboradi
        from monitoring.tasks import notify_nearby_employees
        notify_nearby_employees.delay(incident.id)

        return Response(
            {
                'success': True,
                'id': incident.id,
                'card_number': incident.card_number,
                'created': created,
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


# ── Admin uchun (JWT) ─────────────────────────────────────────────

class Incident112AdminListView(APIView):
    """
    GET /api/v1/incidents/112/
    Filter: ?incident_type_id=  ?priority_id=  ?date=YYYY-MM-DD
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Incident112.objects.all().order_by('-created_time')

        if v := request.query_params.get('incident_type_id'):
            qs = qs.filter(incident_type_id=v)
        if v := request.query_params.get('priority_id'):
            qs = qs.filter(priority_id=v)
        if v := request.query_params.get('date'):
            qs = qs.filter(created_time__date=v)

        serializer = Incident112ListSerializer(qs[:200], many=True)
        return Response({'count': qs.count(), 'results': serializer.data})


class Incident112AdminDetailView(APIView):
    """GET /api/v1/incidents/112/<pk>/"""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            incident = Incident112.objects.get(pk=pk)
        except Incident112.DoesNotExist:
            return Response({'detail': 'Topilmadi.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(Incident112DetailSerializer(incident).data)


# ── Tablet uchun (JWT) — o'z bildirishnomalar ro'yxati ───────────

class TabletIncidentListView(APIView):
    """
    GET /api/v1/tablet/incidents/
    Foydalanuvchiga yuborilgan hodisa bildirishnomalari ro'yxati.
    Filter: ?is_read=true|false
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Incident112Notification.objects.filter(
            employee=request.user,
        ).select_related('incident').order_by('-sent_at')

        if (v := request.query_params.get('is_read')) is not None:
            qs = qs.filter(is_read=v.lower() == 'true')

        serializer = Incident112NotificationSerializer(qs[:100], many=True)
        return Response({'count': qs.count(), 'results': serializer.data})


class TabletIncidentReadView(APIView):
    """
    PATCH /api/v1/tablet/incidents/<pk>/read/
    Bildirishnomani o'qilgan deb belgilaydi.
    """
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        try:
            notif = Incident112Notification.objects.get(pk=pk, employee=request.user)
        except Incident112Notification.DoesNotExist:
            return Response({'detail': 'Topilmadi.'}, status=status.HTTP_404_NOT_FOUND)

        if not notif.is_read:
            notif.is_read = True
            notif.read_at = timezone.now()
            notif.save(update_fields=['is_read', 'read_at'])

        return Response({'success': True})
