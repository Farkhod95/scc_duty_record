from rest_framework import serializers
from fleet.models import TransportType


class TransportTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransportType
        fields = ['id', 'name_uz', 'name_ru', 'name_kaa', 'name_uz_cyrl', 'created_time', 'updated_time']
        read_only_fields = ['created_time', 'updated_time']


class TransportTypeListSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransportType
        fields = ['id', 'name', 'name_uz', 'name_ru', 'name_kaa', 'name_uz_cyrl']