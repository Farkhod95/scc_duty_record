from rest_framework import serializers

from monitoring.models import DutyDay, DutySection, DutySectionAssignment


class DutySectionAssignmentSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    mahalla_name = serializers.CharField(source='mahalla.name', read_only=True, default=None)
    transport_name = serializers.SerializerMethodField()

    class Meta:
        model = DutySectionAssignment
        fields = [
            'id', 'duty_section',
            'mahalla', 'mahalla_name',
            'employee', 'employee_name',
            'transport', 'transport_name',
            'note', 'created_time',
        ]
        read_only_fields = ['id', 'duty_section', 'created_time']

    def get_employee_name(self, obj):
        return str(obj.employee) if obj.employee else None

    def get_transport_name(self, obj):
        return str(obj.transport) if obj.transport else None


class DutySectionSerializer(serializers.ModelSerializer):
    assignments = DutySectionAssignmentSerializer(many=True, read_only=True)
    assignments_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = DutySection
        fields = [
            'id', 'duty_day', 'stage_number', 'name',
            'start_time', 'end_time',
            'assignments_count', 'assignments',
        ]
        read_only_fields = ['id', 'duty_day', 'stage_number']


class DutySectionUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DutySection
        fields = ['name', 'start_time', 'end_time']


class DutyDayCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DutyDay
        fields = ['organization', 'duty_date']

    def validate(self, attrs):
        org = attrs['organization']
        duty_date = attrs['duty_date']
        if DutyDay.objects.filter(organization=org, duty_date=duty_date).exists():
            raise serializers.ValidationError(
                "Bu tashkilot uchun ushbu sana bo'yicha navbatchilik allaqachon mavjud."
            )
        return attrs


class DutyDayListSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    sections_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = DutyDay
        fields = [
            'id', 'organization', 'organization_name',
            'duty_date', 'status', 'status_display',
            'sections_count', 'created_time',
        ]


class DutyDayDetailSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    sections = DutySectionSerializer(many=True, read_only=True)
    submitted_by_name = serializers.SerializerMethodField()
    collected_by_name = serializers.SerializerMethodField()
    approved_by_name = serializers.SerializerMethodField()
    rejected_by_name = serializers.SerializerMethodField()

    class Meta:
        model = DutyDay
        fields = [
            'id', 'organization', 'organization_name',
            'duty_date', 'status', 'status_display',
            'submitted_at', 'submitted_by', 'submitted_by_name',
            'collected_at', 'collected_by', 'collected_by_name',
            'approved_at', 'approved_by', 'approved_by_name',
            'rejected_at', 'rejected_by', 'rejected_by_name',
            'rejection_reason', 'rejected_at_stage',
            'sections',
            'created_time', 'updated_time',
        ]

    def get_submitted_by_name(self, obj):
        return str(obj.submitted_by) if obj.submitted_by else None

    def get_collected_by_name(self, obj):
        return str(obj.collected_by) if obj.collected_by else None

    def get_approved_by_name(self, obj):
        return str(obj.approved_by) if obj.approved_by else None

    def get_rejected_by_name(self, obj):
        return str(obj.rejected_by) if obj.rejected_by else None
