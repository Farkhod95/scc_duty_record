from math import radians, sin, cos, sqrt, asin

from celery import shared_task
from django.conf import settings
from django.utils import timezone


def _haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return R * 2 * asin(sqrt(a))


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def notify_nearby_employees(self, incident_id: int):
    """
    Hodisaga yaqin (radius_km ichida) navbatchi xodimlarni topib,
    WebSocket orqali xabardor qiladi va Incident112Notification yozadi.
    """
    from datetime import date as date_type
    from asgiref.sync import async_to_sync
    from channels.layers import get_channel_layer
    from monitoring.models import Incident112, Incident112Notification, DutySection
    from monitoring.services.grpc_client import grpc_location

    try:
        incident = Incident112.objects.get(id=incident_id)
    except Incident112.DoesNotExist:
        return

    if not incident.latitude or not incident.longitude:
        return

    radius_km = getattr(settings, 'INCIDENT_NOTIFY_RADIUS_KM', 3.0)
    today = date_type.today()

    # Faqat APPROVED statusdagi bugungi navbatchilik xodimlari
    sections = list(
        DutySection.objects.filter(
            duty_day__duty_date=today,
            duty_day__status='APPROVED',
        ).prefetch_related('assignments__employees')
    )

    # pinfl_hash → User mapping
    pinfl_to_user = {}
    for section in sections:
        for asgn in section.assignments.all():
            for emp in asgn.employees.all():
                if emp.pinfl_hash and emp.id not in {u.id for u in pinfl_to_user.values()}:
                    pinfl_to_user[emp.pinfl_hash] = emp

    # gRPC orqali GPS koordinatalarni olib, masofani hisoblash
    nearby = {}  # emp_id → (User, distance_km)
    for section in sections:
        duty_info = grpc_location.duty_info(section.pk)
        if not duty_info:
            continue
        for asgn_info in duty_info.assignments:
            for ei in asgn_info.employees:
                if not ei.latitude or not ei.longitude:
                    continue
                emp = pinfl_to_user.get(ei.pinfl_hash)
                if not emp or emp.id in nearby:
                    continue
                dist = _haversine_km(
                    incident.latitude, incident.longitude,
                    ei.latitude, ei.longitude,
                )
                if dist <= radius_km:
                    nearby[emp.id] = (emp, round(dist, 3))

    if not nearby:
        return

    # WebSocket payload
    incident_payload = {
        'id': incident.id,
        'card_number': incident.card_number,
        'incident_type_id': incident.incident_type_id,
        'incident_description': incident.incident_description,
        'latitude': incident.latitude,
        'longitude': incident.longitude,
        'priority_id': incident.priority_id,
        'fabula': incident.fabula,
        'called_phone': incident.called_phone,
        'created_at': incident.created_time.isoformat(),
    }

    channel_layer = get_channel_layer()

    for emp_id, (emp, dist_km) in nearby.items():
        Incident112Notification.objects.get_or_create(
            incident=incident,
            employee=emp,
            defaults={'distance_km': dist_km},
        )
        async_to_sync(channel_layer.group_send)(
            f'incident_user_{emp_id}',
            {
                'type': 'incident_notification',
                'data': {**incident_payload, 'distance_km': dist_km},
            },
        )
