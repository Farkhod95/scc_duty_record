from rest_framework import serializers
from fleet.models import Transport


class TransportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transport
        fields = [
            'id', 'organization', 'type', 'name_or_code',
            'plate_number', 'capacity', 'number', 'model',
            'created_time', 'updated_time', 'created_by', 'updated_by'
        ]
        read_only_fields = ['id', 'created_time', 'updated_time', 'created_by', 'updated_by']


class TransportListSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    type_name = serializers.CharField(source='type.name', read_only=True)

    class Meta:
        model = Transport
        fields = [
            'id', 'organization', 'organization_name',
            'type', 'type_name',
            'name_or_code', 'plate_number', 'capacity',
            'number', 'model', 'created_time',
        ]
