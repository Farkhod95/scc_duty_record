from rest_framework import serializers

from users.serializers import UserListNotifSerializer
from .models import TranslationTerm, ModelAudit, Notification, ModelChangeLog


class TermSerializer(serializers.ModelSerializer):
    class Meta:
        model = TranslationTerm
        fields = ('id', 'term_name', 'name_uz', 'name_uz_cyrl', 'name_ru', 'name_kaa')
        extra_kwargs = {
            'term_name': {"required": True},
            'name_uz': {"required": True},
            'name_uz_cyrl': {"required": True},
            'name_ru': {"required": True},
            'name_kaa': {"required": True},
        }



class TranslationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TranslationTerm
        fields = ('term_name', 'name')


class ModelAuditSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField(method_name='get_username')

    class Meta:
        model = ModelAudit
        fields = ('id', 'user', 'instance', 'instance_id', 'field_name', 'old_value', 'new_value', 'data', 'action',
                  'timestamp')

    def get_username(self, instance):
        return instance.user.username if instance.user else ''


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ('id', 'title', 'text', 'status', 'created_time', 'updated_time', 'responsible_by', 'updated_by')


class NotificationListSerializer(serializers.ModelSerializer):
    responsible_by_detail = UserListNotifSerializer(source="responsible_by", read_only=True)
    updated_by_detail = UserListNotifSerializer(source="updated_by", read_only=True)

    class Meta:
        model = Notification
        fields = ('id', 'title', 'text', 'status', 'created_time', 'updated_time',
                  'responsible_by','responsible_by_detail', 'updated_by', 'updated_by_detail')


class ModelChangeLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModelChangeLog
        fields = ('id', 'app_label', 'model_name', 'object_id', 'action', 'user', 'data_before', 'data_after', 'user', 'created_at')


class ModelChangeLogListSerializer(serializers.ModelSerializer):
    user_detail = UserListNotifSerializer(source="user", read_only=True)

    class Meta:
        model = ModelChangeLog
        fields = ('id', 'app_label', 'model_name', 'object_id', 'action', 'user', 'data_before', 'data_after', 'user', 'user_detail', 'created_at')