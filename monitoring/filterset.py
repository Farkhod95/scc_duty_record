from django.db.models import Q
from django_filters import FilterSet, DateTimeFilter, DateFilter, CharFilter

from monitoring.models import MainDuty, Task, DutySection, DutySectionType, TaskAssignment, DutyFile, DailyDutyOfficer


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
        if value == 'new':
            return queryset.filter(
                status__in=['DRAFT', 'SENT_FOR_APPROVAL']
            )
        elif value == 'archive':
            return queryset.filter(
                status__in=['APPROVED', 'REJECTED']
            )
        return queryset


class TaskFilter(FilterSet):
    class Meta:
        model = Task
        fields = {
            'task_type': ['exact'],
            'duty_section': ['exact'],
            'location': ['exact'],
            'location__region': ['exact'],
            'location__district': ['exact'],
        }


class DutySectionTypeFilter(FilterSet):
    class Meta:
        model = DutySectionType
        fields = {
            'organization': ['exact'],
            'name': ['exact', 'icontains'],
        }


class DutySectionFilter(FilterSet):
    class Meta:
        model = DutySection
        fields = {
            'main_duty': ['exact'],
            'section_type': ['exact'],
            'name': ['exact', 'icontains'],
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
