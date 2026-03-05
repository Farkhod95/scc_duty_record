import logging
import urllib.request
import urllib.error
import json

from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


def _build_duty_sync_data(main_duty):
    """MainDuty uchun tashqi tizimga yuboriladigan compact JSON."""
    local_tz = timezone.get_current_timezone()

    tasks = main_duty.tasks.select_related('location').prefetch_related(
        'assignments__employee',
        'assignments__transport__type',
    ).order_by('id')

    tasks_data = []
    for task in tasks:
        employees_data = []
        for assignment in task.assignments.all():
            emp = assignment.employee
            employees_data.append({
                'id': emp.id,
                'pinfl_hash': emp.pinfl_hash or '',
                'full_name': emp.get_full_name(),
                'phone': emp.phone_number or '',
                'role': assignment.role_in_transport,
            })

        if task.location:
            location_data = {
                'title': task.location.title,
                'boundary_data': task.location.boundary_data,
            }
        else:
            location_data = None

        tasks_data.append({
            'id': task.id,
            'title': task.title,
            'type': task.task_type,
            'location': location_data,
            'start_time': (
                task.start_time.astimezone(local_tz).isoformat()
                if task.start_time else None
            ),
            'end_time': (
                task.end_time.astimezone(local_tz).isoformat()
                if task.end_time else None
            ),
            'employees': employees_data,
        })

    local_tz = timezone.get_current_timezone()
    return {
        'duty_id': main_duty.id,
        'title': main_duty.title,
        'duty_date': str(main_duty.duty_date),
        'start_time': (
            main_duty.start_time.astimezone(local_tz).isoformat()
            if main_duty.start_time else None
        ),
        'end_time': (
            main_duty.end_time.astimezone(local_tz).isoformat()
            if main_duty.end_time else None
        ),
        'organization': main_duty.organization.name if main_duty.organization else '',
        'tasks': tasks_data,
    }


def send_duty_to_external(main_duty):
    """
    Duty approve bo'lganda tashqi tizimga POST yuboradi.
    EXTERNAL_DUTY_SYNC_URL settings.py da bo'lishi kerak.
    Xatolik bo'lsa approve to'xtatilmaydi, faqat log qilinadi.
    """
    url = getattr(settings, 'EXTERNAL_DUTY_SYNC_URL', None)
    if not url:
        logger.debug("EXTERNAL_DUTY_SYNC_URL sozlanmagan, o'tkazib yuborildi.")
        return

    data = _build_duty_sync_data(main_duty)
    payload = json.dumps(data, ensure_ascii=False).encode('utf-8')

    token = getattr(settings, 'EXTERNAL_SYNC_TOKEN', '')
    headers = {
        'Content-Type': 'application/json; charset=utf-8',
    }
    if token:
        headers['Authorization'] = f'Bearer {token}'

    try:
        req = urllib.request.Request(url, data=payload, headers=headers, method='POST')
        with urllib.request.urlopen(req, timeout=15) as resp:
            status_code = resp.getcode()
            logger.info(f"Duty {main_duty.id} tashqi tizimga yuborildi. Status: {status_code}")
    except urllib.error.HTTPError as e:
        logger.error(f"Duty {main_duty.id} yuborishda HTTP xato: {e.code} {e.reason}")
    except urllib.error.URLError as e:
        logger.error(f"Duty {main_duty.id} yuborishda URL xato: {e.reason}")
    except Exception as e:
        logger.error(f"Duty {main_duty.id} yuborishda kutilmagan xato: {e}")
