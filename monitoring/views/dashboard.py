from django.db.models import Count, Q
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from monitoring.models import DutyDay, Event, DutyDayStatus
from monitoring.serializers.duty_day import DutyDayListSerializer
from monitoring.serializers.event import EventListSerializer


def _duty_day_stats(qs):
    return qs.aggregate(
        total=Count('id'),
        draft=Count('id', filter=Q(status=DutyDayStatus.DRAFT)),
        submitted=Count('id', filter=Q(status=DutyDayStatus.SUBMITTED)),
        collected=Count('id', filter=Q(status=DutyDayStatus.COLLECTED)),
        approved=Count('id', filter=Q(status=DutyDayStatus.APPROVED)),
        rejected=Count('id', filter=Q(status=DutyDayStatus.REJECTED)),
    )


def _event_stats(qs):
    return qs.aggregate(
        total=Count('id'),
        draft=Count('id', filter=Q(status=DutyDayStatus.DRAFT)),
        submitted=Count('id', filter=Q(status=DutyDayStatus.SUBMITTED)),
        collected=Count('id', filter=Q(status=DutyDayStatus.COLLECTED)),
        approved=Count('id', filter=Q(status=DutyDayStatus.APPROVED)),
        rejected=Count('id', filter=Q(status=DutyDayStatus.REJECTED)),
    )


class DashboardView(APIView):
    """
    Rol ga qarab turli ko'rinish qaytaradi.

    OFFICER        → o'z tashkilotining statistikasi + bugungi navbatchilik/tadbir
    COLLECTOR      → tuman bo'yicha SUBMITTED holatdagilar + umumiy statistika
    DISTRICT_ADMIN → tuman bo'yicha COLLECTED holatdagilar + umumiy statistika
    SUPER_ADMIN    → barcha tuman yoki ?district_id=N bilan filtrlash
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        today = timezone.localdate()

        if user.is_super_admin():
            return self._super_admin_view(request, today)

        if user.is_officer():
            return self._officer_view(user, today)

        if user.is_collector():
            return self._district_view(user, today, expected_status=DutyDayStatus.SUBMITTED)

        if user.is_district_admin():
            return self._district_view(user, today, expected_status=DutyDayStatus.COLLECTED)

        return Response({'detail': "Sizning rolingiz uchun dashboard mavjud emas."}, status=403)

    # ── OFFICER ──────────────────────────────────────────────────────────────

    def _officer_view(self, user, today):
        org = user.organization
        if not org:
            return Response({'detail': "Tashkilot biriktirilmagan."}, status=400)

        duty_qs = DutyDay.objects.filter(organization=org)
        event_qs = Event.objects.filter(organization=org)

        today_duty = duty_qs.filter(duty_date=today).annotate(
            sections_count=Count('sections', distinct=True)
        ).first()
        today_events = event_qs.filter(event_date=today).annotate(
            assignments_count=Count('assignments', distinct=True)
        )

        return Response({
            'role': 'OFFICER',
            'organization': org.name,
            'duty_days': _duty_day_stats(duty_qs),
            'events': _event_stats(event_qs),
            'today_duty_day': DutyDayListSerializer(today_duty).data if today_duty else None,
            'today_events': EventListSerializer(today_events, many=True).data,
        })

    # ── COLLECTOR / DISTRICT_ADMIN ────────────────────────────────────────────

    def _district_view(self, user, today, expected_status):
        district = user.district
        if not district:
            return Response({'detail': "Tuman biriktirilmagan."}, status=400)

        duty_qs = DutyDay.objects.filter(organization__district=district)
        event_qs = Event.objects.filter(organization__district=district)

        # Bugungi pending (expected_status + undan oldingilari ham)
        today_duty_days = duty_qs.filter(duty_date=today).annotate(
            sections_count=Count('sections', distinct=True)
        ).select_related('organization').order_by('organization__name')

        today_events = event_qs.filter(event_date=today).annotate(
            assignments_count=Count('assignments', distinct=True)
        ).select_related('organization').order_by('organization__name', 'start_time')

        # Waiting count (nechta tasdiqlash kutmoqda)
        waiting_duty = duty_qs.filter(status=expected_status).count()
        waiting_events = event_qs.filter(status=expected_status).count()

        return Response({
            'role': 'COLLECTOR' if expected_status == DutyDayStatus.SUBMITTED else 'DISTRICT_ADMIN',
            'district': district.name,
            'today': str(today),
            'waiting_duty_days': waiting_duty,
            'waiting_events': waiting_events,
            'duty_day_stats': _duty_day_stats(duty_qs),
            'event_stats': _event_stats(event_qs),
            'today_duty_days': DutyDayListSerializer(today_duty_days, many=True).data,
            'today_events': EventListSerializer(today_events, many=True).data,
        })

    # ── SUPER_ADMIN ───────────────────────────────────────────────────────────

    def _super_admin_view(self, request, today):
        duty_qs = DutyDay.objects.all()
        event_qs = Event.objects.all()

        district_id = request.query_params.get('district_id')
        if district_id:
            duty_qs = duty_qs.filter(organization__district_id=district_id)
            event_qs = event_qs.filter(organization__district_id=district_id)

        today_duty_days = duty_qs.filter(duty_date=today).annotate(
            sections_count=Count('sections', distinct=True)
        ).select_related('organization').order_by('organization__name')

        today_events = event_qs.filter(event_date=today).annotate(
            assignments_count=Count('assignments', distinct=True)
        ).select_related('organization').order_by('organization__name')

        return Response({
            'role': 'SUPER_ADMIN',
            'today': str(today),
            'duty_day_stats': _duty_day_stats(duty_qs),
            'event_stats': _event_stats(event_qs),
            'today_duty_days': DutyDayListSerializer(today_duty_days, many=True).data,
            'today_events': EventListSerializer(today_events, many=True).data,
        })
