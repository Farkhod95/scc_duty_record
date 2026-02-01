from django_filters import FilterSet

from fleet.models import TransportType, Transport


class TransportTypeFilter(FilterSet):
    class Meta:
        model = TransportType
        fields = {
            'name': ['exact', 'icontains'],
        }


class TransportFilter(FilterSet):
    class Meta:
        model = Transport
        fields = {
            'number': ['exact', 'icontains'],
            'model': ['exact', 'icontains'],
            'organization': ['exact'],
            'type': ['exact'],
        }