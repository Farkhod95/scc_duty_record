from rest_framework import status
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, get_object_or_404
from rest_framework.response import Response

from monitoring.models import TaskAssignment, Task, MainDutyStatus
from monitoring.serializers.task_assignment import TaskAssignmentSerializer, TaskAssignmentListSerializer
from monitoring.filterset import TaskAssignmentFilter
from django_filters.rest_framework import DjangoFilterBackend
from restapp.pagination import ResultsSetPagination
from restapp.utils.responses import nonContent
from users.utils.permissions import IsOrgAdmin


class TaskAssignmentView(ListCreateAPIView):
    serializer_class = TaskAssignmentListSerializer
    permission_classes = [IsOrgAdmin]
    pagination_class = ResultsSetPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = TaskAssignmentFilter

    def get_task(self):
        queryset = Task.objects.select_related(
            'duty_section__main_duty__organization'
        )
        if not self.request.user.is_superuser:
            queryset = queryset.filter(
                duty_section__main_duty__organization=self.request.user.organization
            )
        return get_object_or_404(queryset, id=self.kwargs['task_id'])

    def get_queryset(self):
        task = self.get_task()
        return TaskAssignment.objects.filter(
            task=task
        ).select_related('employee', 'transport')

    def post(self, request, task_id):
        task = self.get_task()

        if task.duty_section.main_duty.status != MainDutyStatus.DRAFT:
            return Response(
                {'detail': "Faqat DRAFT holatdagi navbatchilikka tayinlash mumkin."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = request.data.copy()
        data['task'] = task.id
        serializer = TaskAssignmentSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=request.user)
        return Response(serializer.data, status.HTTP_201_CREATED)


class TaskAssignmentDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = TaskAssignmentSerializer
    permission_classes = [IsOrgAdmin]

    def get_queryset(self):
        queryset = TaskAssignment.objects.select_related(
            'task__duty_section__main_duty__organization', 'employee', 'transport'
        )
        if not self.request.user.is_superuser:
            queryset = queryset.filter(
                task__duty_section__main_duty__organization=self.request.user.organization
            )
        return queryset.filter(task_id=self.kwargs['task_id'])

    def get(self, request, task_id, pk):
        instance = get_object_or_404(self.get_queryset(), id=pk)
        serializer = TaskAssignmentListSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, task_id, pk):
        instance = get_object_or_404(self.get_queryset(), id=pk)

        if instance.task.duty_section.main_duty.status != MainDutyStatus.DRAFT:
            return Response(
                {'detail': "Faqat DRAFT holatdagi navbatchilik tayinlashini tahrirlash mumkin."},
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
