from django.db.models import Count
from django.http import HttpResponse
from django.utils.text import get_valid_filename
from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from monitoring.models import Event, EventAssignment, DutyDayStatus, RejectedAtStage
from monitoring.serializers.event import (
    EventCreateSerializer,
    EventUpdateSerializer,
    EventListSerializer,
    EventDetailSerializer,
    EventAssignmentSerializer,
)
from monitoring.services.event_service import (
    submit_event,
    collect_event,
    approve_event,
    reject_event,
)
from users.utils.permissions import IsOfficer, IsCollector, IsDistrictAdmin, IsDistrictLevel


def _event_qs(user):
    qs = Event.objects.select_related('organization', 'created_by').annotate(
        assignments_count=Count('assignments', distinct=True)
    )
    if not user.is_super_admin():
        qs = qs.filter(organization=user.organization)
    return qs


def _event_detail_qs(user):
    qs = Event.objects.select_related(
        'organization', 'created_by',
        'submitted_by', 'collected_by', 'approved_by', 'rejected_by',
    ).prefetch_related(
        'assignments__employees',
        'assignments__mahallas',
        'assignments__transports',
    )
    if not user.is_super_admin():
        qs = qs.filter(organization=user.organization)
    return qs


class EventListCreateView(APIView):
    permission_classes = [IsOfficer]

    def get(self, request):
        from django.utils import timezone
        qs = _event_qs(request.user).order_by('-event_date')

        date = request.query_params.get('date')
        if date:
            qs = qs.filter(event_date=date)

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
                qs = qs.filter(event_date__lt=today)
            elif view_type == 'new':
                qs = qs.filter(event_date__gte=today)

        return Response(EventListSerializer(qs, many=True).data)

    def post(self, request):
        serializer = EventCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        org = serializer.validated_data['organization']
        if not request.user.is_super_admin() and org != request.user.organization:
            return Response(
                {'detail': "Siz faqat o'z tashkilotingiz uchun tadbir yarata olasiz."},
                status=status.HTTP_403_FORBIDDEN,
            )

        event = serializer.save(created_by=request.user)
        event = get_object_or_404(_event_detail_qs(request.user), pk=event.pk)
        return Response(EventDetailSerializer(event).data, status=status.HTTP_201_CREATED)


class EventDetailView(APIView):
    permission_classes = [IsOfficer]

    def get(self, request, pk):
        event = get_object_or_404(_event_detail_qs(request.user), pk=pk)
        return Response(EventDetailSerializer(event).data)

    def patch(self, request, pk):
        event = get_object_or_404(_event_qs(request.user), pk=pk)
        if event.status != DutyDayStatus.DRAFT:
            return Response(
                {'detail': "Faqat DRAFT holatidagi tadbirni tahrirlash mumkin."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = EventUpdateSerializer(event, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=request.user)
        event = get_object_or_404(_event_detail_qs(request.user), pk=pk)
        return Response(EventDetailSerializer(event).data)

    def delete(self, request, pk):
        event = get_object_or_404(_event_qs(request.user), pk=pk)
        if event.status != DutyDayStatus.DRAFT:
            return Response(
                {'detail': "Faqat DRAFT holatidagi tadbirni o'chirish mumkin."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        event.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class EventAssignmentListCreateView(APIView):
    permission_classes = [IsOfficer]

    def _get_event(self, user, pk):
        qs = Event.objects.select_related('organization')
        if not user.is_super_admin():
            qs = qs.filter(organization=user.organization)
        return get_object_or_404(qs, pk=pk)

    def get(self, request, event_id):
        event = self._get_event(request.user, event_id)
        assignments = event.assignments.prefetch_related('employees', 'mahallas', 'transports')
        return Response(EventAssignmentSerializer(assignments, many=True).data)

    def post(self, request, event_id):
        event = self._get_event(request.user, event_id)
        if event.status != DutyDayStatus.DRAFT:
            return Response(
                {'detail': "Faqat DRAFT holatidagi tadbirga biriktirish mumkin."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = EventAssignmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        org = event.organization
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

        assignment = serializer.save(event=event, created_by=request.user)
        return Response(EventAssignmentSerializer(assignment).data, status=status.HTTP_201_CREATED)


class EventAssignmentDetailView(APIView):
    permission_classes = [IsOfficer]

    def _get_assignment(self, user, pk):
        qs = EventAssignment.objects.select_related(
            'event__organization',
        ).prefetch_related('employees', 'mahallas', 'transports')
        if not user.is_super_admin():
            qs = qs.filter(event__organization=user.organization)
        return get_object_or_404(qs, pk=pk)

    def patch(self, request, pk):
        assignment = self._get_assignment(request.user, pk)
        if assignment.event.status != DutyDayStatus.DRAFT:
            return Response(
                {'detail': "Faqat DRAFT holatidagi tayinlashni tahrirlash mumkin."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        org = assignment.event.organization
        serializer = EventAssignmentSerializer(assignment, data=request.data, partial=True)
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
        return Response(EventAssignmentSerializer(assignment).data)

    def delete(self, request, pk):
        assignment = self._get_assignment(request.user, pk)
        if assignment.event.status != DutyDayStatus.DRAFT:
            return Response(
                {'detail': "Faqat DRAFT holatidagi tayinlashni o'chirish mumkin."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        assignment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── Tasdiqlash zanjiri ──────────────────────────────────────

class EventSubmitView(APIView):
    permission_classes = [IsOfficer]

    def post(self, request, pk):
        qs = Event.objects.prefetch_related('assignments__employees')
        if not request.user.is_super_admin():
            qs = qs.filter(organization=request.user.organization)
        event = get_object_or_404(qs, pk=pk)
        try:
            submit_event(event, request.user)
        except ValueError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'detail': "Tadbir tasdiqlashga yuborildi."})


class EventCollectView(APIView):
    permission_classes = [IsCollector]

    def post(self, request, pk):
        qs = Event.objects.select_related('organization')
        if not request.user.is_super_admin():
            qs = qs.filter(organization__district=request.user.district)
        event = get_object_or_404(qs, pk=pk)
        try:
            collect_event(event, request.user)
        except ValueError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'detail': "Tadbir yig'uvchi tomonidan tasdiqlandi."})


class EventApproveView(APIView):
    permission_classes = [IsDistrictAdmin]

    def post(self, request, pk):
        qs = Event.objects.select_related('organization')
        if not request.user.is_super_admin():
            qs = qs.filter(organization__district=request.user.district)
        event = get_object_or_404(qs, pk=pk)
        try:
            approve_event(event, request.user)
        except ValueError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'detail': "Tadbir tuman admin tomonidan tasdiqlandi."})


class EventRejectView(APIView):
    permission_classes = [IsCollector | IsDistrictAdmin]

    def post(self, request, pk):
        qs = Event.objects.select_related('organization')
        if not request.user.is_super_admin():
            qs = qs.filter(organization__district=request.user.district)
        event = get_object_or_404(qs, pk=pk)

        reason = request.data.get('rejection_reason', '').strip()
        if not reason:
            return Response(
                {'detail': "rejection_reason maydoni majburiy."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        stage = RejectedAtStage.COLLECTOR if request.user.is_collector() else RejectedAtStage.DISTRICT_ADMIN

        try:
            reject_event(event, request.user, reason, stage)
        except ValueError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'detail': "Tadbir rad etildi."})


# ── PDF ─────────────────────────────────────────────────────

class EventPdfView(APIView):
    permission_classes = [IsOfficer | IsDistrictLevel]

    def get(self, request, pk):
        event = get_object_or_404(_event_detail_qs(request.user), pk=pk)
        from monitoring.services.duty_day_pdf_service import generate_event_pdf
        pdf_bytes = generate_event_pdf(event)
        filename = get_valid_filename(
            f"event_{event.organization.name}_{event.event_date}_{event.title}.pdf"
        )
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
