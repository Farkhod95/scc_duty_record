from datetime import date as date_type

from django.db.models import Prefetch
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from monitoring.models import (
    DutyDay, DutySection, DutySectionAssignment,
    DutyDayStatus, Event, EventAssignment,
    DailyDutyOfficer, TerritoryExitLog,
)


def _parse_date(request):
    date_str = request.query_params.get('date')
    if date_str:
        try:
            return date_type.fromisoformat(date_str)
        except ValueError:
            pass
    return timezone.localdate()


def _smena_section_rows(sections, active_exit_ids: set, today):
    rows = []
    total_assigned = total_present = total_left = total_incidents = 0

    for section in sections:
        emp_ids = set()
        for assignment in section.assignments.all():
            for emp in assignment.employees.all():
                emp_ids.add(emp.id)

        assigned = len(emp_ids)
        left = len(emp_ids & active_exit_ids)
        present = assigned - left
        incidents = TerritoryExitLog.objects.filter(
            employee_id__in=emp_ids,
            exit_time__date=today,
        ).count()

        if present > 0:
            status = "JOYIDA"
        elif assigned > 0:
            status = "CHIQDI"
        else:
            status = "BO'SH"

        rows.append({
            "id": section.id,
            "name": section.name,
            "stage_number": section.stage_number,
            "start_time": section.start_time,
            "end_time": section.end_time,
            "assigned": assigned,
            "present": present,
            "left": left,
            "incidents": incidents,
            "status": status,
        })
        total_assigned += assigned
        total_present += present
        total_left += left
        total_incidents += incidents

    return {
        "summary": {"present": total_present, "left": total_left},
        "sections": rows,
        "totals": {
            "assigned": total_assigned,
            "present": total_present,
            "left": total_left,
            "incidents": total_incidents,
        },
    }


def _officer_row(daily_officer, active_exit_ids: set):
    user = daily_officer.officer
    status = "CHIQDI" if user.id in active_exit_ids else "JOYIDA"
    return {
        "id": user.id,
        "name": user.get_full_name(),
        "position": user.position.name if user.position else None,
        "organization": daily_officer.organization.name if daily_officer.organization else None,
        "status": status,
        "note": daily_officer.note,
    }


def _event_block(event_qs, today):
    now = timezone.now()
    pending_statuses = [DutyDayStatus.DRAFT, DutyDayStatus.SUBMITTED, DutyDayStatus.COLLECTED]

    planned = event_qs.filter(status__in=pending_statuses).count()
    completed = event_qs.filter(status=DutyDayStatus.APPROVED).count()
    rejected = event_qs.filter(status=DutyDayStatus.REJECTED).count()
    delayed = event_qs.filter(end_time__lt=now, status__in=pending_statuses).count()

    day_events = (
        event_qs
        .filter(event_date=today)
        .select_related('organization')
        .prefetch_related(
            Prefetch(
                'assignments',
                queryset=EventAssignment.objects.prefetch_related('employees'),
            )
        )
        .order_by('start_time')
    )

    events_list = []
    for ev in day_events:
        participant_count = sum(a.employees.count() for a in ev.assignments.all())
        events_list.append({
            "id": ev.id,
            "title": ev.title,
            "organization": ev.organization.name if ev.organization else None,
            "start_time": ev.start_time.strftime("%H:%M") if ev.start_time else None,
            "end_time": ev.end_time.strftime("%H:%M") if ev.end_time else None,
            "status": ev.status,
            "participant_count": participant_count,
        })

    return {
        "stats": {
            "planned": planned,
            "completed": completed,
            "rejected": rejected,
            "delayed": delayed,
        },
        "selected_date": str(today),
        "events_by_date": events_list,
    }


class AdminDashboardView(APIView):
    """
    GET /api/v1/admin-dashboard/
    Query params:
      date=YYYY-MM-DD   — qaysi kun (default: bugun)
      district_id=N     — faqat SUPER_ADMIN uchun tuman filtr

    Javob tarkibi:
      smena_statistics  — bo'linmalar bo'yicha (tayinlangan/joyida/chiqib ketgan/hodisalar)
      district_officers — tuman navbatchilari va ularning holati
      events            — tadbirlar statistikasi + tanlangan sana ro'yxati

    Rol bo'yicha scope:
      OFFICER        → o'z tashkiloti
      COLLECTOR      → o'z tumani
      DISTRICT_ADMIN → o'z tumani
      SUPER_ADMIN    → hammasi (yoki ?district_id=N)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        today = _parse_date(request)

        active_exit_ids = set(
            TerritoryExitLog.objects.filter(
                exit_time__date=today,
                return_time__isnull=True,
            ).values_list('employee_id', flat=True)
        )

        return Response({
            "date": str(today),
            "smena_statistics": self._smena(user, request, today, active_exit_ids),
            "district_officers": self._officers(user, today, active_exit_ids),
            "events": self._events(user, request, today),
        })

    # ── Smena statistikasi ──────────────────────────────────────────────────

    def _smena(self, user, request, today, active_exit_ids):
        duty_days = self._duty_day_qs(user, request, today)
        if duty_days is None:
            return self._empty_smena()

        sections = DutySection.objects.filter(
            duty_day__in=duty_days
        ).prefetch_related(
            Prefetch(
                'assignments',
                queryset=DutySectionAssignment.objects.prefetch_related('employees'),
            )
        ).order_by('duty_day', 'stage_number')

        return _smena_section_rows(sections, active_exit_ids, today)

    def _duty_day_qs(self, user, request, today):
        if user.is_super_admin():
            qs = DutyDay.objects.filter(duty_date=today)
            district_id = request.query_params.get('district_id')
            if district_id:
                qs = qs.filter(organization__district_id=district_id)
            return qs
        if user.is_officer():
            if not user.organization:
                return None
            return DutyDay.objects.filter(organization=user.organization, duty_date=today)
        district = user.district
        if not district:
            return None
        return DutyDay.objects.filter(organization__district=district, duty_date=today)

    def _empty_smena(self):
        return {
            "summary": {"present": 0, "left": 0},
            "sections": [],
            "totals": {"assigned": 0, "present": 0, "left": 0, "incidents": 0},
        }

    # ── Tuman navbatchilari ─────────────────────────────────────────────────

    def _officers(self, user, today, active_exit_ids):
        qs = DailyDutyOfficer.objects.filter(duty_date=today).select_related(
            'officer', 'officer__position', 'organization'
        )

        district = self._resolve_district(user)
        if district:
            qs = qs.filter(organization__district=district)

        officers = []
        present = left = 0
        for duty_officer in qs:
            row = _officer_row(duty_officer, active_exit_ids)
            officers.append(row)
            if row["status"] == "CHIQDI":
                left += 1
            else:
                present += 1

        total = len(officers)
        active_percent = round(present / total * 100) if total else 0

        return {
            "total": total,
            "present": present,
            "left": left,
            "active_percent": active_percent,
            "officers": officers,
        }

    def _resolve_district(self, user):
        if user.is_super_admin():
            return None
        if user.district:
            return user.district
        if user.organization and user.organization.district:
            return user.organization.district
        return None

    # ── Faol tadbirlar ──────────────────────────────────────────────────────

    def _events(self, user, request, today):
        if user.is_super_admin():
            qs = Event.objects.all()
            district_id = request.query_params.get('district_id')
            if district_id:
                qs = qs.filter(organization__district_id=district_id)
            return _event_block(qs, today)

        if user.is_officer():
            if not user.organization:
                return self._empty_events(today)
            return _event_block(Event.objects.filter(organization=user.organization), today)

        district = user.district
        if not district:
            return self._empty_events(today)
        return _event_block(Event.objects.filter(organization__district=district), today)

    def _empty_events(self, today):
        return {
            "stats": {"planned": 0, "completed": 0, "rejected": 0, "delayed": 0},
            "selected_date": str(today),
            "events_by_date": [],
        }
