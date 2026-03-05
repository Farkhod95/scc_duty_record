from rest_framework import serializers

from monitoring.models import Event, EventAssignment, DutyDayStatus


class EventAssignmentSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    transport_name = serializers.SerializerMethodField()
    role_in_transport_display = serializers.CharField(
        source='get_role_in_transport_display', read_only=True
    )

    class Meta:
        model = EventAssignment
        fields = [
            'id', 'event',
            'employee', 'employee_name',
            'transport', 'transport_name',
            'role_in_transport', 'role_in_transport_display',
            'note', 'created_time',
        ]
        read_only_fields = ['id', 'event', 'created_time']

    def get_employee_name(self, obj):
        return str(obj.employee) if obj.employee else None

    def get_transport_name(self, obj):
        return str(obj.transport) if obj.transport else None


class EventCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = [
            'organization', 'title', 'event_date',
            'start_time', 'end_time', 'mahalla', 'description',
        ]

    def validate(self, attrs):
        start = attrs.get('start_time')
        end = attrs.get('end_time')
        if start and end and start >= end:
            raise serializers.ValidationError(
                {"end_time": "Tugash vaqti boshlanish vaqtidan keyin bo'lishi kerak."}
            )
        return attrs


class EventUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ['title', 'event_date', 'start_time', 'end_time', 'mahalla', 'description']

    def validate(self, attrs):
        instance = self.instance
        start = attrs.get('start_time', instance.start_time if instance else None)
        end = attrs.get('end_time', instance.end_time if instance else None)
        if start and end and start >= end:
            raise serializers.ValidationError(
                {"end_time": "Tugash vaqti boshlanish vaqtidan keyin bo'lishi kerak."}
            )
        return attrs


class EventListSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    mahalla_name = serializers.CharField(source='mahalla.name', read_only=True, default=None)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    assignments_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Event
        fields = [
            'id', 'organization', 'organization_name',
            'title', 'event_date', 'start_time', 'end_time',
            'mahalla', 'mahalla_name',
            'status', 'status_display',
            'assignments_count', 'created_time',
        ]


class EventDetailSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    mahalla_name = serializers.CharField(source='mahalla.name', read_only=True, default=None)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    assignments = EventAssignmentSerializer(many=True, read_only=True)
    submitted_by_name = serializers.SerializerMethodField()
    collected_by_name = serializers.SerializerMethodField()
    approved_by_name = serializers.SerializerMethodField()
    rejected_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = [
            'id', 'organization', 'organization_name',
            'title', 'event_date', 'start_time', 'end_time',
            'mahalla', 'mahalla_name', 'description',
            'status', 'status_display',
            'submitted_at', 'submitted_by', 'submitted_by_name',
            'collected_at', 'collected_by', 'collected_by_name',
            'approved_at', 'approved_by', 'approved_by_name',
            'rejected_at', 'rejected_by', 'rejected_by_name',
            'rejection_reason', 'rejected_at_stage',
            'assignments',
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
