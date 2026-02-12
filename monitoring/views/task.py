from django.db.models import Count
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, filters
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, get_object_or_404
from rest_framework.response import Response

from monitoring.models import Task, DutySection, MainDutyStatus
from monitoring.serializers.task import TaskSerializer, TaskListSerializer, TaskDetailSerializer
from monitoring.filterset import TaskFilter
from restapp.pagination import ResultsSetPagination
from restapp.utils.responses import nonContent
from users.utils.permissions import IsOrgAdmin


class TaskView(ListCreateAPIView):
    serializer_class = TaskListSerializer
    permission_classes = [IsOrgAdmin]
    pagination_class = ResultsSetPagination
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = TaskFilter
    search_fields = ('title', 'location')

    def get_section(self):
        queryset = DutySection.objects.select_related('main_duty__organization')
        if not self.request.user.is_superuser:
            queryset = queryset.filter(
                main_duty__organization=self.request.user.organization
            )
        return get_object_or_404(queryset, id=self.kwargs['section_id'])

    def get_queryset(self):
        section = self.get_section()
        return Task.objects.filter(
            duty_section=section
        ).annotate(assignments_count=Count('assignments'))

    def post(self, request, section_id):
        section = self.get_section()

        if section.main_duty.status != MainDutyStatus.DRAFT:
            return Response(
                {'detail': "Faqat DRAFT holatdagi navbatchilikka vazifa qo'shish mumkin."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = request.data.copy()
        data['duty_section'] = section.id
        serializer = TaskSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=request.user)
        return Response(serializer.data, status.HTTP_201_CREATED)


class TaskDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = TaskSerializer
    permission_classes = [IsOrgAdmin]

    def get_queryset(self):
        queryset = Task.objects.select_related(
            'duty_section__main_duty__organization'
        )
        if not self.request.user.is_superuser:
            queryset = queryset.filter(
                duty_section__main_duty__organization=self.request.user.organization
            )
        return queryset.filter(duty_section_id=self.kwargs['section_id'])

    def get(self, request, section_id, pk):
        instance = get_object_or_404(self.get_queryset(), id=pk)
        serializer = TaskDetailSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, section_id, pk):
        instance = get_object_or_404(self.get_queryset(), id=pk)

        if instance.duty_section.main_duty.status != MainDutyStatus.DRAFT:
            return Response(
                {'detail': "Faqat DRAFT holatdagi navbatchilik vazifasini tahrirlash mumkin."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = request.data.copy()
        data['duty_section'] = section_id
        serializer = self.serializer_class(instance, data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=request.user)
        return Response(serializer.data, status.HTTP_202_ACCEPTED)

    def delete(self, request, section_id, pk):
        instance = get_object_or_404(self.get_queryset(), id=pk)
        instance.delete()
        return Response(nonContent(), status.HTTP_204_NO_CONTENT)
