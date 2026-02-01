from rest_framework import serializers
from fleet.models import TransportType


class TransportTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransportType
        fields = ['id', 'name', 'icon_url', 'created_time', 'updated_time']
        read_only_fields = ['created_time', 'updated_time']


class TransportTypeListSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransportType
        fields = ['id', 'name', 'icon_url']