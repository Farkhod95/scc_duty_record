import logging

from django.conf import settings
from django.utils import timezone
from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from monitoring.models import DutySection
from monitoring.services.microservice import send_section_started, send_section_ended
from tablet.auth import IsTabletSessionValid
from tablet.models import DutyCheckIn
from tablet.serializers import TabletSectionSerializer, DutyCheckInSerializer, TodaySectionSerializer, TabletMeSerializer

logger = logging.getLogger(__name__)


class TabletPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        page_num = self.page.number
        total_pages = self.page.paginator.num_pages
        return Response({
            'total_count': self.page.paginator.count,
            'total_pages': total_pages,
            'page': page_num,
            'page_size': self.get_page_size(self.request),
            'next_page': page_num + 1 if self.page.has_next() else None,
            'prev_page': page_num - 1 if self.page.has_previous() else None,
            'results': data,
        })


class TabletMeView(APIView):
    """GET /api/v1/me/ — Kirgan foydalanuvchining o'z ma'lumotlari."""
    permission_classes = [IsTabletSessionValid]

    def get(self, request):
        user = request.user.__class__.objects.select_related(
            'organization__region',
            'organization__district',
            'position',
            'department',
            'special_rank',
        ).get(pk=request.user.pk)
        return Response(TabletMeSerializer(user, context={'request': request}).data)


class TabletMyDutyView(APIView):
    """
    Navbatchining o'z navbatchiligi.
    GET ?type=new  → bugun va keyingi kunlar
    GET ?type=archive → o'tgan kunlar
    """
    permission_classes = [IsTabletSessionValid]

    def get(self, request):
        today = timezone.localdate()
        view_type = request.query_params.get('type', 'new')

        sections = DutySection.objects.filter(
            assignments__employees=request.user,
            duty_day__status='APPROVED',
        ).select_related(
            'duty_day__organization',
        ).prefetch_related(
            'assignments__employees',
            'assignments__transports',
            'assignments__location__mahallas',
            'assignments__location__points',
            'checkins',
        ).distinct()

        if view_type == 'archive':
            sections = sections.filter(duty_day__duty_date__lt=today)
        else:
            sections = sections.filter(duty_day__duty_date__gte=today)

        sections = sections.order_by('duty_day__duty_date', 'stage_number')

        paginator = TabletPagination()
        page = paginator.paginate_queryset(sections, request)
        serializer = TabletSectionSerializer(page, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)


class TabletTodayDutyView(APIView):
    """
    GET /api/v1/duty/today/
    Bugungi navbatchilik — to'liq ma'lumot.
    """
    permission_classes = [IsTabletSessionValid]

    def get(self, request):
        today = timezone.localdate()
        sections = DutySection.objects.filter(
            assignments__employees=request.user,
            duty_day__duty_date=today,
            duty_day__status='APPROVED',
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
    permission_classes = [IsTabletSessionValid]

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

        send_section_started(section)
        return Response(DutyCheckInSerializer(checkin).data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class TabletDutyEndView(APIView):
    """POST — navbatchilikni tugatish."""
    permission_classes = [IsTabletSessionValid]

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
        send_section_ended(checkin.duty_section)
        return Response(DutyCheckInSerializer(checkin).data)


class TabletConfigView(APIView):
    """GET /api/v1/config/ — Planshet sozlamalari."""
    permission_classes = [IsTabletSessionValid]

    def get(self, request):
        return Response({
            'location_interval': settings.TABLET_LOCATION_INTERVAL,
        })


class TabletLocationView(APIView):
    """POST /api/v1/location/ — GPS joylashuvni yuborish."""
    permission_classes = [IsTabletSessionValid]

    def post(self, request):
        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')
        if latitude is None or longitude is None:
            return Response({'detail': 'latitude va longitude majburiy.'}, status=status.HTTP_400_BAD_REQUEST)

        if not request.user.pinfl_hash:
            return Response({'detail': 'Foydalanuvchi pinfl_hash si yo\'q.'}, status=status.HTTP_400_BAD_REQUEST)

        from monitoring.services.grpc_client import grpc_location
        grpc_location.send_location(
            pinfl_hash=request.user.pinfl_hash,
            latitude=float(latitude),
            longitude=float(longitude),
            accuracy=float(request.data.get('accuracy') or 0),
            timestamp=int(request.data.get('timestamp') or 0),
        )
        return Response(status=status.HTTP_204_NO_CONTENT)
