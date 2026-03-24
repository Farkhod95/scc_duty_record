from django.utils import timezone
from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from monitoring.models import DutySection
from tablet.models import DutyCheckIn
from tablet.serializers import TabletSectionSerializer, DutyCheckInSerializer, TodaySectionSerializer


class TabletMyDutyView(APIView):
    """
    Navbatchining o'z navbatchiligi.
    GET ?type=new  → bugun va keyingi kunlar
    GET ?type=archive → o'tgan kunlar
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = timezone.localdate()
        view_type = request.query_params.get('type', 'new')

        sections = DutySection.objects.filter(
            assignments__employees=request.user,
            duty_day__status__in=['SUBMITTED', 'COLLECTED', 'APPROVED'],
        ).select_related(
            'duty_day__organization',
        ).prefetch_related(
            'assignments__employees',
            'assignments__location__mahallas',
            'assignments__transports',
            'checkins',
        ).distinct()

        if view_type == 'archive':
            sections = sections.filter(duty_day__duty_date__lt=today)
        else:
            sections = sections.filter(duty_day__duty_date__gte=today)

        sections = sections.order_by('duty_day__duty_date', 'stage_number')
        return Response(TabletSectionSerializer(sections, many=True, context={'request': request}).data)


class TabletTodayDutyView(APIView):
    """
    GET /api/v1/duty/today/
    Bugungi navbatchilik — to'liq ma'lumot:
    location (boundary_data, mahallalar boundary_data bilan, points), xodimlar, transportlar, check-in holati.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = timezone.localdate()
        sections = DutySection.objects.filter(
            assignments__employees=request.user,
            duty_day__duty_date=today,
            duty_day__status__in=['SUBMITTED', 'COLLECTED', 'APPROVED'],
        ).select_related(
            'duty_day__organization',
        ).prefetch_related(
            'assignments__employees',
            'assignments__transports',
            'assignments__location__mahallas',
            'assignments__location__points',
            'checkins',
        ).distinct().order_by('stage_number')

        return Response(TodaySectionSerializer(sections, many=True, context={'request': request}).data)


class TabletDutyStartView(APIView):
    """POST — navbatchilikni boshlash."""
    permission_classes = [IsAuthenticated]

    def post(self, request, section_id):
        section = get_object_or_404(
            DutySection.objects.select_related('duty_day'),
            pk=section_id,
            assignments__employees=request.user,
        )

        checkin, created = DutyCheckIn.objects.get_or_create(
            employee=request.user,
            duty_section=section,
            defaults={'check_in_time': timezone.now()},
        )

        if not created:
            if checkin.check_out_time is not None:
                return Response(
                    {'detail': "Bu bosqich allaqachon yakunlangan."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if checkin.check_in_time is not None:
                return Response(
                    {'detail': "Navbatchilik allaqachon boshlangan."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            checkin.check_in_time = timezone.now()
            checkin.save(update_fields=['check_in_time'])

        return Response(DutyCheckInSerializer(checkin).data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class TabletDutyEndView(APIView):
    """POST — navbatchilikni tugatish."""
    permission_classes = [IsAuthenticated]

    def post(self, request, section_id):
        checkin = get_object_or_404(
            DutyCheckIn,
            employee=request.user,
            duty_section_id=section_id,
            check_in_time__isnull=False,
            check_out_time__isnull=True,
        )
        checkin.check_out_time = timezone.now()
        checkin.save(update_fields=['check_out_time'])
        return Response(DutyCheckInSerializer(checkin).data)
