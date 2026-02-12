from django_filters import FilterSet, DateTimeFilter, DateFilter

from monitoring.models import MainDuty, Task, DutySection, TaskAssignment, DailyDutyOfficer


class MainDutyFilter(FilterSet):
    duty_date_from = DateFilter(field_name='duty_date', lookup_expr='gte')
    duty_date_to = DateFilter(field_name='duty_date', lookup_expr='lte')
    start_time_from = DateTimeFilter(field_name='start_time', lookup_expr='gte')
    start_time_to = DateTimeFilter(field_name='start_time', lookup_expr='lte')

    class Meta:
        model = MainDuty
        fields = {
            'title': ['exact', 'icontains'],
            'organization': ['exact'],
            'status': ['exact'],
        }


class TaskFilter(FilterSet):
    class Meta:
        model = Task
        fields = {
            'task_type': ['exact'],
            'duty_section': ['exact'],
        }


class DutySectionFilter(FilterSet):
    class Meta:
        model = DutySection
        fields = {
            'main_duty': ['exact'],
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


class DailyDutyOfficerFilter(FilterSet):
    class Meta:
        model = DailyDutyOfficer
        fields = {
            'organization': ['exact'],
            'officer': ['exact'],
            'duty_date': ['exact', 'gte', 'lte'],
        }
