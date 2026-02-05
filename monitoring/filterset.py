from django_filters import FilterSet, DateTimeFilter
from monitoring.models import DutyCategory, Duty


class DutyCategoryFilter(FilterSet):
    class Meta:
        model = DutyCategory
        fields = {
            'name': ['exact', 'icontains'],
            'is_active': ['exact'],
        }


class DutyFilter(FilterSet):
    start_time_from = DateTimeFilter(field_name='start_time', lookup_expr='gte')
    start_time_to = DateTimeFilter(field_name='start_time', lookup_expr='lte')
    end_time_from = DateTimeFilter(field_name='end_time', lookup_expr='gte')
    end_time_to = DateTimeFilter(field_name='end_time', lookup_expr='lte')

    class Meta:
        model = Duty
        fields = {
            'name': ['exact', 'icontains'],
            'organization': ['exact'],
            'location': ['exact'],
            'category': ['exact'],
            'status': ['exact'],
        }