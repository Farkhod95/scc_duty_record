from rest_framework import serializers

from monitoring.models import MainDuty, MainDutyStatus


class MainDutySerializer(serializers.ModelSerializer):
    class Meta:
        model = MainDuty
        fields = [
            'id', 'organization', 'title', 'duty_date', 'start_time', 'end_time',
            'status', 'approved_by', 'approved_at', 'rejection_reason',
            'created_time', 'updated_time', 'created_by', 'updated_by',
        ]
        read_only_fields = [
            'id', 'status', 'approved_by', 'approved_at', 'rejection_reason',
            'created_time', 'updated_time', 'created_by', 'updated_by',
        ]


class MainDutyListSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    sections_count = serializers.IntegerField(read_only=True)
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = MainDuty
        fields = [
            'id', 'organization', 'organization_name', 'title',
            'duty_date', 'start_time', 'end_time',
            'status', 'status_display', 'sections_count',
            'created_by', 'created_by_name', 'created_time',
        ]

    def get_created_by_name(self, obj):
        if obj.created_by:
            return obj.created_by.get_full_name()
        return None


class MainDutyDetailSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    approved_by_name = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()
    sections = serializers.SerializerMethodField()
    files = serializers.SerializerMethodField()

    class Meta:
        model = MainDuty
        fields = [
            'id', 'organization', 'organization_name', 'title',
            'duty_date', 'start_time', 'end_time',
            'status', 'status_display',
            'approved_by', 'approved_by_name', 'approved_at', 'rejection_reason',
            'created_by', 'created_by_name', 'created_time', 'updated_time',
            'sections', 'files',
        ]

    def get_approved_by_name(self, obj):
        if obj.approved_by:
            return obj.approved_by.get_full_name()
        return None

    def get_created_by_name(self, obj):
        if obj.created_by:
            return obj.created_by.get_full_name()
        return None

    def get_sections(self, obj):
        from monitoring.serializers.duty_section import DutySectionDetailSerializer
        sections = obj.sections.prefetch_related(
            'tasks__assignments__employee', 'tasks__assignments__transport'
        ).all()
        return DutySectionDetailSerializer(sections, many=True).data

    def get_files(self, obj):
        from monitoring.serializers.duty_file import DutyFileListSerializer
        return DutyFileListSerializer(obj.files.all(), many=True).data
