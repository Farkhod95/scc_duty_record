from django_filters.rest_framework import FilterSet, DateFilter

from restapp.models import ModelAudit, Notification, ModelChangeLog


class ModelAuditFilter(FilterSet):

    class Meta:
        model = ModelAudit
        fields = ['module', 'instance', 'instance_id']


class NotificationFilter(FilterSet):

    class Meta:
        model = Notification
        fields = {
            'status': ['exact'],
            'responsible_by': ['exact'],
            'updated_by': ['exact'],
        }


class ModelChangeLogFilter(FilterSet):
    date_from = DateFilter(
        field_name='created_at',
        lookup_expr='date__gte',
        label='Boshlanish sanasi'
    )

    # ?date_to=2025-01-31 => created_at <= 2025-01-31 23:59:59
    date_to = DateFilter(
        field_name='created_at',
        lookup_expr='date__lte',
        label='Tugash sanasi'
    )

    class Meta:
        model = ModelChangeLog
        fields = {
            'model_name': ['exact'],
            'object_id': ['exact'],
            'user': ['exact'],
            'action': ['exact'],
            'created_at': ['exact'],
        }