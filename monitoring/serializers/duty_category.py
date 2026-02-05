from rest_framework import serializers
from monitoring.models import DutyCategory


class DutyCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = DutyCategory
        fields = [
            'id', 'name', 'description', 'is_active', 'is_manu',
            'created_time', 'updated_time', 'created_by', 'updated_by'
        ]
        read_only_fields = ['id', 'created_time', 'updated_time', 'created_by', 'updated_by']


class DutyCategoryListSerializer(serializers.ModelSerializer):
    class Meta:
        model = DutyCategory
        fields = ['id', 'name', 'is_manu', 'is_active']