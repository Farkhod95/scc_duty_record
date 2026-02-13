from rest_framework import serializers

from monitoring.models import Task


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = [
            'id', 'duty_section', 'title', 'task_type',
            'start_time', 'end_time', 'location', 'description',
            'created_time', 'updated_time', 'created_by', 'updated_by',
        ]
        read_only_fields = ['id', 'created_time', 'updated_time', 'created_by', 'updated_by']


class TaskListSerializer(serializers.ModelSerializer):
    task_type_display = serializers.CharField(source='get_task_type_display', read_only=True)
    assignments_count = serializers.IntegerField(read_only=True)
    location_name = serializers.CharField(source='location.title', read_only=True, default=None)
    region = serializers.IntegerField(source='location.region_id', read_only=True, default=None)
    region_name = serializers.CharField(source='location.region.name', read_only=True, default=None)
    district = serializers.IntegerField(source='location.district_id', read_only=True, default=None)
    district_name = serializers.CharField(source='location.district.name', read_only=True, default=None)

    class Meta:
        model = Task
        fields = [
            'id', 'duty_section', 'title', 'task_type', 'task_type_display',
            'start_time', 'end_time',
            'location', 'location_name', 'region', 'region_name', 'district', 'district_name',
            'description', 'assignments_count', 'created_time',
        ]


class TaskDetailSerializer(serializers.ModelSerializer):
    task_type_display = serializers.CharField(source='get_task_type_display', read_only=True)
    assignments = serializers.SerializerMethodField()
    location_name = serializers.CharField(source='location.title', read_only=True, default=None)
    region = serializers.IntegerField(source='location.region_id', read_only=True, default=None)
    region_name = serializers.CharField(source='location.region.name', read_only=True, default=None)
    district = serializers.IntegerField(source='location.district_id', read_only=True, default=None)
    district_name = serializers.CharField(source='location.district.name', read_only=True, default=None)

    class Meta:
        model = Task
        fields = [
            'id', 'duty_section', 'title', 'task_type', 'task_type_display',
            'start_time', 'end_time',
            'location', 'location_name', 'region', 'region_name', 'district', 'district_name',
            'description', 'assignments', 'created_time', 'updated_time',
        ]

    def get_assignments(self, obj):
        from monitoring.serializers.task_assignment import TaskAssignmentListSerializer
        return TaskAssignmentListSerializer(obj.assignments.all(), many=True).data
