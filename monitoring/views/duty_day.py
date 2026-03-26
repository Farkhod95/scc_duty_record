from django.db.models import Count
from django.http import HttpResponse
from django.utils import timezone
from django.utils.text import get_valid_filename
from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from monitoring.models import DutyDay, DutySection, DutySectionAssignment, DutyDayStatus
from monitoring.serializers.duty_day import (
    DutyDayCreateSerializer,
    DutyDayListSerializer,
    DutyDayDetailSerializer,
    DutySectionSerializer,
    DutySectionUpdateSerializer,
    DutySectionAssignmentSerializer,
)
from monitoring.services.duty_day_service import (
    create_duty_day_with_sections,
    submit_duty_day,
    collect_duty_day,
    approve_duty_day,
    reject_duty_day,
)
from users.utils.permissions import IsOfficer, IsCollector, IsDistrictAdmin, IsDistrictLevel


def _duty_day_qs(user):
    qs = DutyDay.objects.select_related('organization', 'created_by').annotate(
        sections_count=Count('sections', distinct=True)
    )
    if not user.is_super_admin():
        qs = qs.filter(organization=user.organization)
    return qs


def _duty_day_detail_qs(user):
    qs = DutyDay.objects.select_related(
        'organization',
        'submitted_by', 'collected_by', 'approved_by', 'rejected_by',
    ).prefetch_related(
        'sections__assignments__employees',
        'sections__assignments__location',
        'sections__assignments__transports',
    )
    if not user.is_super_admin():
        qs = qs.filter(organization=user.organization)
    return qs


class DutyDayListCreateView(APIView):
    permission_classes = [IsOfficer]

    def get(self, request):
        qs = _duty_day_qs(request.user).order_by('-duty_date')

        date = request.query_params.get('date')
        if date:
            qs = qs.filter(duty_date=date)

        status_param = request.query_params.get('status')
        if status_param:
            qs = qs.filter(status=status_param)

        org_param = request.query_params.get('organization')
        if org_param and request.user.is_super_admin():
            qs = qs.filter(organization_id=org_param)

        view_type = request.query_params.get('type')
        if view_type:
            today = timezone.localdate()
            if view_type == 'archive':
                qs = qs.filter(duty_date__lt=today)
            elif view_type == 'new':
                qs = qs.filter(duty_date__gte=today)

        return Response(DutyDayListSerializer(qs, many=True).data)

    def post(self, request):
        serializer = DutyDayCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        org = serializer.validated_data['organization']
        duty_date = serializer.validated_data['duty_date']

        if not request.user.is_super_admin() and org != request.user.organization:
            return Response(
                {'detail': "Siz faqat o'z tashkilotingiz uchun navbatchilik yarata olasiz."},
                status=status.HTTP_403_FORBIDDEN,
            )

        duty_day = create_duty_day_with_sections(org, duty_date, request.user)
        duty_day = get_object_or_404(_duty_day_detail_qs(request.user), pk=duty_day.pk)
        return Response(DutyDayDetailSerializer(duty_day).data, status=status.HTTP_201_CREATED)


class DutyDayDetailView(APIView):
    permission_classes = [IsOfficer]

    def get(self, request, pk):
        duty_day = get_object_or_404(_duty_day_detail_qs(request.user), pk=pk)
        return Response(DutyDayDetailSerializer(duty_day).data)

    def delete(self, request, pk):
        duty_day = get_object_or_404(_duty_day_qs(request.user), pk=pk)
        if duty_day.status != DutyDayStatus.DRAFT:
            return Response(
                {'detail': "Faqat DRAFT holatidagi navbatchilikni o'chirish mumkin."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        duty_day.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class DutySectionDetailView(APIView):
    permission_classes = [IsOfficer]

    def _get_section(self, user, pk):
        qs = DutySection.objects.select_related(
            'duty_day__organization'
        ).prefetch_related(
            'assignments__employees',
            'assignments__location',
            'assignments__transports',
        ).annotate(assignments_count=Count('assignments', distinct=True))
        if not user.is_super_admin():
            qs = qs.filter(duty_day__organization=user.organization)
        return get_object_or_404(qs, pk=pk)

    def get(self, request, pk):
        section = self._get_section(request.user, pk)
        return Response(DutySectionSerializer(section).data)

    def patch(self, request, pk):
        section = self._get_section(request.user, pk)
        if section.duty_day.status != DutyDayStatus.DRAFT:
            return Response(
                {'detail': "Faqat DRAFT holatidagi seksiyani tahrirlash mumkin."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = DutySectionUpdateSerializer(section, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=request.user)
        section.refresh_from_db()
        return Response(DutySectionSerializer(section).data)


class DutySectionAssignmentListCreateView(APIView):
    permission_classes = [IsOfficer]

    def _get_section(self, user, section_id):
        qs = DutySection.objects.select_related('duty_day__organization')
        if not user.is_super_admin():
            qs = qs.filter(duty_day__organization=user.organization)
        return get_object_or_404(qs, pk=section_id)

    def get(self, request, section_id):
        section = self._get_section(request.user, section_id)
        assignments = section.assignments.prefetch_related('employees', 'transports').select_related('location')
        return Response(DutySectionAssignmentSerializer(assignments, many=True).data)

    def post(self, request, section_id):
        section = self._get_section(request.user, section_id)
        if section.duty_day.status != DutyDayStatus.DRAFT:
            return Response(
                {'detail': "Faqat DRAFT holatidagi seksiyaga biriktirish mumkin."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = DutySectionAssignmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        org = section.duty_day.organization
        employees = serializer.validated_data.get('employees', [])
        transports = serializer.validated_data.get('transports', [])

        for emp in employees:
            if emp.organization_id != org.pk:
                return Response(
                    {'detail': f"Xodim '{emp}' bu tashkilotga tegishli emas."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        for t in transports:
            if t.organization_id != org.pk:
                return Response(
                    {'detail': f"Transport '{t}' bu tashkilotga tegishli emas."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        assignment = serializer.save(duty_section=section, created_by=request.user)
        return Response(DutySectionAssignmentSerializer(assignment).data, status=status.HTTP_201_CREATED)


class DutySectionAssignmentDetailView(APIView):
    permission_classes = [IsOfficer]

    def _get_assignment(self, user, pk):
        qs = DutySectionAssignment.objects.select_related(
            'duty_section__duty_day__organization', 'location',
        ).prefetch_related('employees', 'transports')
        if not user.is_super_admin():
            qs = qs.filter(duty_section__duty_day__organization=user.organization)
        return get_object_or_404(qs, pk=pk)

    def patch(self, request, pk):
        assignment = self._get_assignment(request.user, pk)
        if assignment.duty_section.duty_day.status != DutyDayStatus.DRAFT:
            return Response(
                {'detail': "Faqat DRAFT holatidagi tayinlashni tahrirlash mumkin."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        org = assignment.duty_section.duty_day.organization
        serializer = DutySectionAssignmentSerializer(assignment, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        for emp in serializer.validated_data.get('employees', []):
            if emp.organization_id != org.pk:
                return Response(
                    {'detail': f"Xodim '{emp}' bu tashkilotga tegishli emas."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        for t in serializer.validated_data.get('transports', []):
            if t.organization_id != org.pk:
                return Response(
                    {'detail': f"Transport '{t}' bu tashkilotga tegishli emas."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        serializer.save(updated_by=request.user)
        assignment.refresh_from_db()
        return Response(DutySectionAssignmentSerializer(assignment).data)

    def delete(self, request, pk):
        assignment = self._get_assignment(request.user, pk)
        if assignment.duty_section.duty_day.status != DutyDayStatus.DRAFT:
            return Response(
                {'detail': "Faqat DRAFT holatidagi tayinlashni o'chirish mumkin."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        assignment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ============================================================
# Etap 4 — Tasdiqlash zanjiri
# ============================================================

class DutyDaySubmitView(APIView):
    permission_classes = [IsOfficer]

    def post(self, request, pk):
        qs = DutyDay.objects.prefetch_related('sections__assignments__employees')
        if not request.user.is_super_admin():
            qs = qs.filter(organization=request.user.organization)
        duty_day = get_object_or_404(qs, pk=pk)
        try:
            submit_duty_day(duty_day, request.user)
        except ValueError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'detail': "Navbatchilik tasdiqlashga yuborildi."})


class DutyDayCollectView(APIView):
    permission_classes = [IsCollector]

    def post(self, request, pk):
        qs = DutyDay.objects.select_related('organization')
        if not request.user.is_super_admin():
            qs = qs.filter(organization__district=request.user.district)
        duty_day = get_object_or_404(qs, pk=pk)
        try:
            collect_duty_day(duty_day, request.user)
        except ValueError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'detail': "Navbatchilik yig'uvchi tomonidan tasdiqlandi."})


class DutyDayApproveView(APIView):
    permission_classes = [IsDistrictAdmin]

    def post(self, request, pk):
        qs = DutyDay.objects.select_related('organization')
        if not request.user.is_super_admin():
            qs = qs.filter(organization__district=request.user.district)
        duty_day = get_object_or_404(qs, pk=pk)
        try:
            approve_duty_day(duty_day, request.user)
        except ValueError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'detail': "Navbatchilik tuman admin tomonidan tasdiqlandi."})


class DutyDayRejectView(APIView):
    permission_classes = [IsCollector | IsDistrictAdmin]

    def post(self, request, pk):
        qs = DutyDay.objects.select_related('organization')
        if not request.user.is_super_admin():
            qs = qs.filter(organization__district=request.user.district)
        duty_day = get_object_or_404(qs, pk=pk)

        reason = request.data.get('rejection_reason', '').strip()
        if not reason:
            return Response(
                {'detail': "rejection_reason maydoni majburiy."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from monitoring.models import RejectedAtStage
        stage = RejectedAtStage.COLLECTOR if request.user.is_collector() else RejectedAtStage.DISTRICT_ADMIN

        try:
            reject_duty_day(duty_day, request.user, reason, stage)
        except ValueError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'detail': "Navbatchilik rad etildi."})


# ============================================================
# Tuman ko'rinishi
# ============================================================

class DistrictDutyView(APIView):
    permission_classes = [IsDistrictLevel]

    def get(self, request):
        from monitoring.models import Event
        from monitoring.serializers.event import EventDetailSerializer

        view_type = request.query_params.get('type')
        if view_type not in ('archive', 'new'):
            return Response(
                {'detail': "type parametri majburiy: 'archive' yoki 'new'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if request.user.is_super_admin():
            district_id = request.query_params.get('district_id')
            if not district_id:
                return Response(
                    {'detail': "Super admin uchun district_id parametri majburiy."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            district_filter = {'organization__district_id': district_id}
        else:
            district_filter = {'organization__district': request.user.district}

        base_duty_qs = DutyDay.objects.filter(
            **district_filter,
        ).select_related(
            'organization',
            'submitted_by', 'collected_by', 'approved_by', 'rejected_by',
        ).prefetch_related(
            'sections__assignments__employees',
            'sections__assignments__location',
            'sections__assignments__transports',
        ).order_by('duty_date', 'organization__name')

        base_event_qs = Event.objects.filter(
            **district_filter,
        ).select_related(
            'organization',
            'submitted_by', 'collected_by', 'approved_by', 'rejected_by',
        ).prefetch_related(
            'assignments__employees',
            'assignments__mahallas',
            'assignments__transports',
        ).order_by('event_date', 'organization__name', 'start_time')

        today = timezone.localdate()
        if view_type == 'archive':
            duty_days = base_duty_qs.filter(duty_date__lt=today)
            events = base_event_qs.filter(event_date__lt=today)
        else:
            duty_days = base_duty_qs.filter(duty_date__gte=today)
            events = base_event_qs.filter(event_date__gte=today)

        if not request.user.is_super_admin():
            if request.user.is_collector():
                allowed_statuses = [
                    DutyDayStatus.SUBMITTED,
                    DutyDayStatus.COLLECTED,
                    DutyDayStatus.APPROVED,
                ]
            else:  # district_admin
                allowed_statuses = [
                    DutyDayStatus.COLLECTED,
                    DutyDayStatus.APPROVED,
                ]
            duty_days = duty_days.filter(status__in=allowed_statuses)
            events = events.filter(status__in=allowed_statuses)

        return Response({
            'duty_days': DutyDayDetailSerializer(duty_days, many=True).data,
            'events': EventDetailSerializer(events, many=True).data,
        })


class DistrictDutyDetailView(APIView):
    permission_classes = [IsDistrictLevel]

    def get(self, request, pk):
        if request.user.is_super_admin():
            qs = DutyDay.objects.all()
        else:
            qs = DutyDay.objects.filter(organization__district=request.user.district)
            if request.user.is_collector():
                qs = qs.filter(status__in=[
                    DutyDayStatus.SUBMITTED,
                    DutyDayStatus.COLLECTED,
                    DutyDayStatus.APPROVED,
                ])
            else:  # district_admin
                qs = qs.filter(status__in=[
                    DutyDayStatus.COLLECTED,
                    DutyDayStatus.APPROVED,
                ])

        duty_day = get_object_or_404(
            qs.select_related(
                'organization',
                'submitted_by', 'collected_by', 'approved_by', 'rejected_by',
            ).prefetch_related(
                'sections__assignments__employees',
                'sections__assignments__location',
                'sections__assignments__transports',
            ),
            pk=pk,
        )
        return Response(DutyDayDetailSerializer(duty_day).data)


# ============================================================
# PDF
# ============================================================

class DutyDayPdfView(APIView):
    permission_classes = [IsOfficer | IsDistrictLevel]

    def get(self, request, pk):
        duty_day = get_object_or_404(_duty_day_detail_qs(request.user), pk=pk)
        from monitoring.services.duty_day_pdf_service import generate_duty_day_pdf
        pdf_bytes = generate_duty_day_pdf(duty_day)
        filename = get_valid_filename(
            f"duty_{duty_day.organization.name}_{duty_day.duty_date}.pdf"
        )
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
