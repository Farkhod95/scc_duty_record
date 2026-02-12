from rest_framework import serializers

from monitoring.models import DailyDutyOfficer


class DailyDutyOfficerSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyDutyOfficer
        fields = [
            'id', 'organization', 'officer', 'duty_date', 'note',
            'assigned_by', 'created_time',
        ]
        read_only_fields = ['id', 'assigned_by', 'created_time']

    def validate(self, attrs):
        officer = attrs.get('officer')
        organization = attrs.get('organization')

        if officer and organization:
            if officer.organization_id != organization.id:
                raise serializers.ValidationError({
                    'officer': "Dijur admin tashkilotga tegishli bo'lishi kerak."
                })

        return attrs


class DailyDutyOfficerListSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    officer_full_name = serializers.SerializerMethodField()
    assigned_by_name = serializers.SerializerMethodField()

    class Meta:
        model = DailyDutyOfficer
        fields = [
            'id', 'organization', 'organization_name',
            'officer', 'officer_full_name',
            'duty_date', 'note',
            'assigned_by', 'assigned_by_name',
            'created_time',
        ]

    def get_officer_full_name(self, obj):
        if obj.officer:
            return obj.officer.get_full_name()
        return None

    def get_assigned_by_name(self, obj):
        if obj.assigned_by:
            return obj.assigned_by.get_full_name()
        return None
