from django.db.models import Count, Prefetch, Q
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework.generics import ListAPIView

from directory.models import Location
from monitoring.filterset import LocationTasksFilter
from monitoring.models import Task, TaskAssignment, MainDutyStatus
from monitoring.serializers.location_tasks import LocationWithTasksSerializer
from restapp.pagination import ResultsSetPagination
from users.utils.permissions import IsOrgAdmin


class LocationTasksView(ListAPIView):
    serializer_class = LocationWithTasksSerializer
    permission_classes = [IsOrgAdmin]
    pagination_class = ResultsSetPagination
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = LocationTasksFilter
    search_fields = ('title', 'key')

    def get_queryset(self):
        user = self.request.user
        params = self.request.query_params

        duty_date = params.get('duty_date', timezone.localdate().isoformat())
        status_filter = params.get('status', MainDutyStatus.APPROVED)
        task_type = params.get('task_type')
        organization = params.get('organization')

        task_filters = Q(
            main_duty__duty_date=duty_date,
            main_duty__status=status_filter,
        )

        location_task_filters = Q(
            tasks__main_duty__duty_date=duty_date,
            tasks__main_duty__status=status_filter,
        )

        if user.is_superuser and organization:
            task_filters &= Q(main_duty__organization_id=organization)
            location_task_filters &= Q(tasks__main_duty__organization_id=organization)
        elif not user.is_superuser:
            task_filters &= Q(main_duty__organization=user.organization)
            location_task_filters &= Q(tasks__main_duty__organization=user.organization)

        if task_type:
            task_filters &= Q(task_type=task_type)
            location_task_filters &= Q(tasks__task_type=task_type)

        task_qs = Task.objects.filter(task_filters).select_related(
            'main_duty__organization',
        ).prefetch_related(
            Prefetch(
                'assignments',
                queryset=TaskAssignment.objects.select_related('employee', 'transport'),
            )
        )

        return Location.objects.select_related(
            'region', 'district',
        ).prefetch_related(
            Prefetch('tasks', queryset=task_qs, to_attr='filtered_tasks'),
        ).annotate(
            tasks_count=Count('tasks', filter=location_task_filters),
        ).filter(
            tasks_count__gt=0,
        ).order_by('title')
