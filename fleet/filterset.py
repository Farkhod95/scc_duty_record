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
            'plate_number': ['exact', 'icontains'],
            'name_or_code': ['exact', 'icontains'],
            'organization': ['exact'],
            'type': ['exact'],
        }
