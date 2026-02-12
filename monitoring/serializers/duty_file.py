from rest_framework import serializers

from monitoring.models import DutyFile


class DutyFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = DutyFile
        fields = [
            'id', 'main_duty', 'file', 'name',
            'created_time', 'updated_time', 'created_by', 'updated_by',
        ]
        read_only_fields = ['id', 'created_time', 'updated_time', 'created_by', 'updated_by']


class DutyFileListSerializer(serializers.ModelSerializer):
    class Meta:
        model = DutyFile
        fields = ['id', 'main_duty', 'file', 'name', 'created_time']
