from django.contrib.auth import get_user_model
from rest_framework import serializers

from directory.models import Mahalla
from fleet.models import Transport
from monitoring.models import DutyDay, DutySection, DutySectionAssignment

User = get_user_model()


class DutySectionAssignmentSerializer(serializers.ModelSerializer):
    employees = serializers.PrimaryKeyRelatedField(
        many=True, queryset=User.objects.all(), required=False
    )
    mahallas = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Mahalla.objects.all(), required=False
    )
    transports = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Transport.objects.all(), required=False
    )
    employees_detail = serializers.SerializerMethodField()
    mahallas_detail = serializers.SerializerMethodField()
    transports_detail = serializers.SerializerMethodField()

    class Meta:
        model = DutySectionAssignment
        fields = [
            'id', 'duty_section',
            'employees', 'employees_detail',
            'mahallas', 'mahallas_detail',
            'transports', 'transports_detail',
            'note', 'created_time',
        ]
        read_only_fields = ['id', 'duty_section', 'created_time']

    def get_employees_detail(self, obj):
        return [{'id': e.pk, 'name': str(e)} for e in obj.employees.all()]

    def get_mahallas_detail(self, obj):
        return [{'id': m.pk, 'name': m.name} for m in obj.mahallas.all()]

    def get_transports_detail(self, obj):
        return [{'id': t.pk, 'name': str(t)} for t in obj.transports.all()]

    def create(self, validated_data):
        employees = validated_data.pop('employees', [])
        mahallas = validated_data.pop('mahallas', [])
        transports = validated_data.pop('transports', [])
        instance = super().create(validated_data)
        instance.employees.set(employees)
        instance.mahallas.set(mahallas)
        instance.transports.set(transports)
        return instance

    def update(self, instance, validated_data):
        employees = validated_data.pop('employees', None)
        mahallas = validated_data.pop('mahallas', None)
        transports = validated_data.pop('transports', None)
        instance = super().update(instance, validated_data)
        if employees is not None:
            instance.employees.set(employees)
        if mahallas is not None:
            instance.mahallas.set(mahallas)
        if transports is not None:
            instance.transports.set(transports)
        return instance


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
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = DutyDay
        fields = [
            'id', 'organization', 'organization_name',
            'duty_date', 'status', 'status_display',
            'sections_count',
            'created_by', 'created_by_name',
            'created_time',
        ]

    def get_created_by_name(self, obj):
        return str(obj.created_by) if obj.created_by else None


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
