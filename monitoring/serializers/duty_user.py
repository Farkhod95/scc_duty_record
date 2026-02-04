from rest_framework import serializers
from monitoring.models import DutyUser
from django.contrib.auth import get_user_model

User = get_user_model()


class DutyUserSerializer(serializers.ModelSerializer):
    user_full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    transport_number = serializers.CharField(source='transport.number', read_only=True)
    transport_model = serializers.CharField(source='transport.model', read_only=True)

    class Meta:
        model = DutyUser
        fields = [
            'id', 'duty', 'user', 'user_full_name', 'user_username',
            'transport', 'transport_number', 'transport_model',
            'is_driver', 'is_notified', 'notified_at',
            'check_in_time', 'check_in_photo', 'check_in_lat',
            'check_in_lon', 'check_in_verified',
            'check_out_time', 'check_out_lat', 'check_out_lon',
            'current_status', 'created_time', 'updated_time'
        ]
        read_only_fields = [
            'id', 'duty', 'user_full_name', 'user_username',
            'transport_number', 'transport_model',
            'is_notified', 'notified_at', 'check_in_time',
            'check_in_photo', 'check_in_lat', 'check_in_lon',
            'check_in_verified', 'check_out_time', 'check_out_lat',
            'check_out_lon', 'current_status', 'created_time', 'updated_time'
        ]


class DutyUserCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DutyUser
        fields = ['user', 'transport', 'is_driver']

    def validate(self, data):
        if data.get('transport') and not data.get('is_driver'):
            pass
        return data


class DutyUserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DutyUser
        fields = ['transport', 'is_driver']


class DutyUserListSerializer(serializers.ModelSerializer):
    user_full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    transport_number = serializers.CharField(source='transport.number', read_only=True, allow_null=True)
    transport_model = serializers.CharField(source='transport.model', read_only=True, allow_null=True)
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = DutyUser
        fields = [
            'id', 'user', 'user_full_name',
            'transport', 'transport_number',
            'is_driver', 'current_status',
            'avatar', 'transport_model'
        ]

    def get_avatar(self, obj):
        if obj.user and obj.user.avatar:
            try:
                return obj.user.avatar.url
            except ValueError:
                return None
        return None