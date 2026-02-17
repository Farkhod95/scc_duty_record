from django.db.models import Q
from django.utils import timezone
from django_filters import FilterSet, DateTimeFilter, DateFilter, CharFilter

from monitoring.models import MainDuty, Task, TaskAssignment, DutyFile, DailyDutyOfficer


class MainDutyFilter(FilterSet):
    duty_date_from = DateFilter(field_name='duty_date', lookup_expr='gte')
    duty_date_to = DateFilter(field_name='duty_date', lookup_expr='lte')
    start_time_from = DateTimeFilter(field_name='start_time', lookup_expr='gte')
    start_time_to = DateTimeFilter(field_name='start_time', lookup_expr='lte')
    list_type = CharFilter(method='filter_list_type')

    class Meta:
        model = MainDuty
        fields = {
            'title': ['exact', 'icontains'],
            'organization': ['exact'],
            'status': ['exact'],
            'created_by': ['exact'],
        }

    def filter_list_type(self, queryset, name, value):
        today = timezone.localdate()
        if value == 'today':
            return queryset.filter(duty_date=today)
        elif value == 'archive':
            return queryset.filter(duty_date__lt=today)
        return queryset


class TaskFilter(FilterSet):
    class Meta:
        model = Task
        fields = {
            'task_type': ['exact'],
            'main_duty': ['exact'],
            'location': ['exact'],
            'location__region': ['exact'],
            'location__district': ['exact'],
        }


class TaskAssignmentFilter(FilterSet):
    class Meta:
        model = TaskAssignment
        fields = {
            'task': ['exact'],
            'employee': ['exact'],
            'transport': ['exact'],
            'role_in_transport': ['exact'],
        }


class DutyFileFilter(FilterSet):
    class Meta:
        model = DutyFile
        fields = {
            'name': ['exact', 'icontains'],
        }


class DailyDutyOfficerFilter(FilterSet):
    class Meta:
        model = DailyDutyOfficer
        fields = {
            'organization': ['exact'],
            'officer': ['exact'],
            'duty_date': ['exact', 'gte', 'lte'],
            'assigned_by': ['exact'],
        }
