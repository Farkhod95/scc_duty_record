from rest_framework import serializers
from monitoring.models import Duty
from monitoring.serializers.duty_category import DutyCategoryListSerializer
from monitoring.serializers.duty_user import DutyUserListSerializer


class DutySerializer(serializers.ModelSerializer):
    class Meta:
        model = Duty
        fields = [
            'id', 'organization', 'mahalla', 'category', 'name',
            'start_time', 'end_time', 'status', 'file',
            'approved_by', 'approved_at', 'rejection_reason',
            'created_time', 'updated_time', 'created_by', 'updated_by'
        ]
        read_only_fields = [
            'id', 'status', 'approved_by', 'approved_at', 'rejection_reason',
            'created_time', 'updated_time', 'created_by', 'updated_by'
        ]


class DutyListSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    mahalla_name = serializers.CharField(source='mahalla.name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_type = serializers.CharField(source='category.type', read_only=True)
    users_count = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Duty
        fields = [
            'id', 'organization', 'organization_name', 'mahalla', 'mahalla_name',
            'category', 'category_name', 'category_type', 'name',
            'start_time', 'end_time', 'status', 'status_display',
            'users_count', 'created_time'
        ]

    def get_users_count(self, obj):
        return obj.duty_users.count()


class DutyDetailSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    mahalla_name = serializers.CharField(source='mahalla.name', read_only=True)
    category_detail = DutyCategoryListSerializer(source='category', read_only=True)
    duty_users = DutyUserListSerializer(many=True, read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.get_full_name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    statistics = serializers.SerializerMethodField()

    class Meta:
        model = Duty
        fields = [
            'id', 'organization', 'organization_name', 'mahalla', 'mahalla_name',
            'category', 'category_detail', 'name', 'start_time', 'end_time',
            'status', 'status_display', 'file',
            'approved_by', 'approved_by_name', 'approved_at',
            'rejection_reason', 'duty_users', 'statistics',
            'created_time', 'updated_time', 'created_by', 'created_by_name', 'updated_by'
        ]

    def get_statistics(self, obj):
        from monitoring.services import duty_service
        return duty_service.get_duty_statistics(obj)


class DutyApproveSerializer(serializers.Serializer):
    """Duty ni tasdiqlash uchun"""
    pass


class DutyRejectSerializer(serializers.Serializer):
    """Duty ni rad etish uchun"""
    reason = serializers.CharField(required=True, help_text="Rad etish sababi")


class DutyCancelSerializer(serializers.Serializer):
    """Duty ni bekor qilish uchun"""
    reason = serializers.CharField(required=True, help_text="Bekor qilish sababi")