"""
Monitoring mikroservisga event yuborish.

Har bir funksiya:
  - Tegishli MICROSERVICE_*_URL sozlanmagan bo'lsa — log qilib o'tkazadi
  - Xatolik bo'lsa — log qilib, asosiy jarayonni to'xtatmaydi
"""
import json
import logging
import urllib.request
import urllib.error

from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Ichki yordamchi
# ---------------------------------------------------------------------------

def _post(url_setting: str, payload: dict, timeout: int = 5) -> None:
    """settings dagi url_setting ga JSON payload POST qiladi."""
    url = getattr(settings, url_setting, '')
    if not url:
        logger.debug("Microservice: %s sozlanmagan, o'tkazib yuborildi.", url_setting)
        return

    token = getattr(settings, 'EXTERNAL_SYNC_TOKEN', '')
    headers = {'Content-Type': 'application/json; charset=utf-8'}
    if token:
        headers['Authorization'] = f'Bearer {token}'

    body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
    req = urllib.request.Request(url, data=body, headers=headers, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            logger.debug("Microservice %s: status=%s", url_setting, resp.status)
    except urllib.error.HTTPError as exc:
        logger.warning("Microservice %s HTTP xato: %s %s", url_setting, exc.code, exc.reason)
    except Exception as exc:
        logger.warning("Microservice %s xato: %s", url_setting, exc)


# ---------------------------------------------------------------------------
# 1. location.sync
# ---------------------------------------------------------------------------

def send_location_sync(location) -> None:
    """
    Location yaratilganda yoki yangilanganda chaqiriladi.

    Event: location.sync
    URL setting: MICROSERVICE_LOCATION_SYNC_URL
    """
    payload = {
        'event': 'location.sync',
        'location': {
            'id': location.id,
            'title': location.title,
            'org_id': location.organization_id,
            'org_name': location.organization.name if location.organization else None,
            'region_id': location.region_id,
            'region_name': location.region.name if location.region else None,
            'district_id': location.district_id,
            'district_name': location.district.name if location.district else None,
            'boundary_data': location.boundary_data,
        },
    }
    _post('MICROSERVICE_LOCATION_SYNC_URL', payload)


# ---------------------------------------------------------------------------
# 2. point.sync
# ---------------------------------------------------------------------------

def send_point_sync(point) -> None:
    """
    LocationPoint yaratilganda yoki yangilanganda chaqiriladi.
    location_id orqali qaysi locationga tegishli ekanligi ko'rsatiladi.

    Event: point.sync
    URL setting: MICROSERVICE_POINT_SYNC_URL
    """
    location = point.location

    payload = {
        'event': 'point.sync',
        'point': {
            'id': point.id,
            'location_id': location.id,
            'order': point.order,
            'name': point.name,
            'latitude': float(point.latitude) if point.latitude is not None else None,
            'longitude': float(point.longitude) if point.longitude is not None else None,
            'start_time': str(point.start_time),
            'end_time': str(point.end_time),
        },
    }
    _post('MICROSERVICE_POINT_SYNC_URL', payload)


# ---------------------------------------------------------------------------
# 3. section.started
# ---------------------------------------------------------------------------

def send_section_started(section) -> None:
    """
    DutySection boshlanganda (TabletDutyStartView) chaqiriladi.
    Har bir DutySectionAssignment alohida element sifatida yuboriladi.
    Xodimlar faqat pinfl_hash bilan yuboriladi.

    Event: section.started
    URL setting: MICROSERVICE_SECTION_STARTED_URL
    """
    local_tz = timezone.get_current_timezone()
    duty_day = section.duty_day
    org = duty_day.organization

    assignments_qs = section.assignments.select_related('location').prefetch_related(
        'employees', 'transports__type'
    )

    assignments_data = []
    for assignment in assignments_qs:
        employee_hashes = [
            {'pinfl_hash': emp.pinfl_hash}
            for emp in assignment.employees.all()
            if emp.pinfl_hash
        ]
        transport_list = [
            {
                'id': tr.id,
                'plate_number': tr.plate_number,
                'model': tr.model,
                'number': tr.number,
                'type_name': tr.type.name if tr.type else None,
            }
            for tr in assignment.transports.all()
        ]
        assignments_data.append({
            'assignment_id': assignment.id,
            'location_id': assignment.location_id,
            'employees': employee_hashes,
            'transports': transport_list,
        })

    started_at = (
        section.start_time.astimezone(local_tz).isoformat()
        if section.start_time
        else timezone.now().astimezone(local_tz).isoformat()
    )

    payload = {
        'event': 'section.started',
        'section_id': section.id,
        'duty_day_id': duty_day.id,
        'duty_date': str(duty_day.duty_date),
        'stage_number': section.stage_number,
        'stage_name': section.name,
        'started_at': started_at,
        'org_id': org.id,
        'org_name': org.name,
        'region_id': org.region_id,
        'district_id': org.district_id,
        'assignments': assignments_data,
    }
    _post('MICROSERVICE_SECTION_STARTED_URL', payload)


# ---------------------------------------------------------------------------
# 4. section.ended
# ---------------------------------------------------------------------------

def send_section_ended(section) -> None:
    """
    DutySection tugaganda (TabletDutyEndView) chaqiriladi.

    Event: section.ended
    URL setting: MICROSERVICE_SECTION_ENDED_URL
    """
    local_tz = timezone.get_current_timezone()

    ended_at = (
        section.end_time.astimezone(local_tz).isoformat()
        if section.end_time
        else timezone.now().astimezone(local_tz).isoformat()
    )

    payload = {
        'event': 'section.ended',
        'section_id': section.id,
        'duty_day_id': section.duty_day_id,
        'ended_at': ended_at,
    }
    _post('MICROSERVICE_SECTION_ENDED_URL', payload)
