from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, filters
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from monitoring.models import TaskAssignment, Task, MainDutyStatus, AbsenceRequest, AbsenceRequestStatus
from monitoring.serializers.task_assignment import (
    TaskAssignmentSerializer, TaskAssignmentListSerializer,
    AbsenceRequestSerializer, AbsenceRequestReviewSerializer,
)
from monitoring.filterset import TaskAssignmentFilter
from restapp.pagination import ResultsSetPagination
from restapp.utils.responses import nonContent
from users.utils.permissions import IsOrgAdmin, IsOrgEmployee


class TaskAssignmentView(ListCreateAPIView):
    serializer_class = TaskAssignmentListSerializer
    permission_classes = [IsOrgAdmin]
    pagination_class = ResultsSetPagination
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = TaskAssignmentFilter
    search_fields = ('employee__first_name', 'employee__last_name')

    def get_task(self):
        queryset = Task.objects.select_related(
            'main_duty__organization'
        )
        if not self.request.user.is_superuser:
            queryset = queryset.filter(
                main_duty__organization=self.request.user.organization
            )
        return get_object_or_404(queryset, id=self.kwargs['task_id'])

    def get_queryset(self):
        task = self.get_task()
        return TaskAssignment.objects.filter(
            task=task
        ).select_related('employee', 'transport')

    def post(self, request, task_id):
        task = self.get_task()

        if task.main_duty.status != MainDutyStatus.DRAFT:
            return Response(
                {'error': "Faqat DRAFT holatdagi navbatchilikka tayinlash mumkin."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = request.data.copy()
        data['task'] = task.id
        serializer = TaskAssignmentSerializer(data=data)
        serializer.is_valid(raise_exception=True)

        employee = serializer.validated_data['employee']
        main_duty = task.main_duty
        new_start = task.start_time or main_duty.start_time
        new_end = task.end_time or main_duty.end_time

        # Auto-transfer: remove employee from conflicting tasks
        existing_assignments = TaskAssignment.objects.filter(
            employee=employee
        ).exclude(task=task).select_related('task__main_duty')

        conflict_ids = []
        for assignment in existing_assignments:
            t = assignment.task
            t_start = t.start_time or t.main_duty.start_time
            t_end = t.end_time or t.main_duty.end_time
            if t_start < new_end and t_end > new_start:
                conflict_ids.append(assignment.id)

        if conflict_ids:
            TaskAssignment.objects.filter(id__in=conflict_ids).delete()

        serializer.save(created_by=request.user)
        return Response(serializer.data, status.HTTP_201_CREATED)


class TaskAssignmentDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = TaskAssignmentSerializer
    permission_classes = [IsOrgAdmin]

    def get_queryset(self):
        queryset = TaskAssignment.objects.select_related(
            'task__main_duty__organization', 'employee', 'transport'
        )
        if not self.request.user.is_superuser:
            queryset = queryset.filter(
                task__main_duty__organization=self.request.user.organization
            )
        return queryset.filter(task_id=self.kwargs['task_id'])

    def get(self, request, task_id, pk):
        instance = get_object_or_404(self.get_queryset(), id=pk)
        serializer = TaskAssignmentListSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, task_id, pk):
        instance = get_object_or_404(self.get_queryset(), id=pk)

        if instance.task.main_duty.status != MainDutyStatus.DRAFT:
            return Response(
                {'error': "Faqat DRAFT holatdagi navbatchilik tayinlashini tahrirlash mumkin."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = request.data.copy()
        data['task'] = task_id
        serializer = self.serializer_class(instance, data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=request.user)
        return Response(serializer.data, status.HTTP_202_ACCEPTED)

    def delete(self, request, task_id, pk):
        instance = get_object_or_404(self.get_queryset(), id=pk)
        instance.delete()
        return Response(nonContent(), status.HTTP_204_NO_CONTENT)


class AbsenceRequestCreateView(APIView):
    """POST: Create an absence request for a task assignment."""
    serializer_class = AbsenceRequestSerializer
    permission_classes = [IsOrgAdmin, IsOrgEmployee]

    def get_assignment(self, task_id, pk):
        queryset = TaskAssignment.objects.select_related(
            'task__main_duty__organization'
        )
        if not self.request.user.is_superuser:
            queryset = queryset.filter(
                task__main_duty__organization=self.request.user.organization
            )
        return get_object_or_404(queryset, task_id=task_id, id=pk)

    def post(self, request, task_id, pk):
        assignment = self.get_assignment(task_id, pk)

        if hasattr(assignment, 'absence_request'):
            return Response(
                {'error': "Bu tayinlash uchun allaqachon so'rov mavjud."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = request.data.copy()
        data['task_assignment'] = assignment.id
        serializer = AbsenceRequestSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def get(self, request, task_id, pk):
        assignment = self.get_assignment(task_id, pk)
        if not hasattr(assignment, 'absence_request'):
            return Response(
                {'error': "Bu tayinlash uchun so'rov topilmadi."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = AbsenceRequestSerializer(assignment.absence_request)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AbsenceRequestReviewView(APIView):
    """PATCH: Admin/manager reviews an absence request."""
    permission_classes = [IsOrgAdmin]

    def get_queryset(self):
        queryset = AbsenceRequest.objects.select_related(
            'task_assignment__task__main_duty__organization',
            'task_assignment__employee',
        )
        if not self.request.user.is_superuser:
            queryset = queryset.filter(
                task_assignment__task__main_duty__organization=self.request.user.organization
            )
        return queryset

    def patch(self, request, pk):
        instance = get_object_or_404(self.get_queryset(), id=pk)
        serializer = AbsenceRequestReviewSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data.get('status')
        replacement = serializer.validated_data.get('replacement_employee')

        serializer.save(reviewed_by=request.user, reviewed_at=timezone.now())

        # If approved with replacement: delete old assignment, create new one
        if new_status == AbsenceRequestStatus.APPROVED and replacement:
            old_assignment = instance.task_assignment
            TaskAssignment.objects.create(
                task=old_assignment.task,
                employee=replacement,
                transport=old_assignment.transport,
                role_in_transport=old_assignment.role_in_transport,
                note=old_assignment.note,
                created_by=request.user,
            )
            old_assignment.delete()

        return Response(serializer.data, status=status.HTTP_200_OK)

    def get(self, request, pk):
        instance = get_object_or_404(self.get_queryset(), id=pk)
        serializer = AbsenceRequestSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)
