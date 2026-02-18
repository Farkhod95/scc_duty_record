from rest_framework import serializers

from directory.models import Location
from monitoring.models import Task, TaskAssignment


class LocationTaskAssignmentSerializer(serializers.ModelSerializer):
    employee_full_name = serializers.SerializerMethodField()
    transport_info = serializers.SerializerMethodField()
    role_display = serializers.CharField(source='get_role_in_transport_display', read_only=True)

    class Meta:
        model = TaskAssignment
        fields = [
            'id', 'employee', 'employee_full_name',
            'transport', 'transport_info', 'role_in_transport', 'role_display',
            'note',
        ]

    def get_employee_full_name(self, obj):
        if obj.employee:
            return obj.employee.get_full_name()
        return None

    def get_transport_info(self, obj):
        if obj.transport:
            return str(obj.transport)
        return None


class LocationTaskSerializer(serializers.ModelSerializer):
    task_type_display = serializers.CharField(source='get_task_type_display', read_only=True)
    main_duty_title = serializers.CharField(source='main_duty.title', read_only=True, default=None)
    organization_name = serializers.CharField(
        source='main_duty.organization.name', read_only=True, default=None
    )
    assignments_count = serializers.SerializerMethodField()
    assignments = LocationTaskAssignmentSerializer(many=True, read_only=True)

    class Meta:
        model = Task
        fields = [
            'id', 'main_duty', 'main_duty_title', 'organization_name',
            'title', 'task_type', 'task_type_display',
            'start_time', 'end_time', 'description',
            'assignments_count', 'assignments',
        ]

    def get_assignments_count(self, obj):
        return obj.assignments.all().count()


class LocationWithTasksSerializer(serializers.ModelSerializer):
    region_name = serializers.CharField(source='region.name', read_only=True, allow_null=True)
    district_name = serializers.CharField(source='district.name', read_only=True, allow_null=True)
    has_boundary = serializers.SerializerMethodField()
    tasks_count = serializers.IntegerField(read_only=True)
    tasks = LocationTaskSerializer(source='filtered_tasks', many=True, read_only=True)

    class Meta:
        model = Location
        fields = [
            'id', 'region', 'region_name', 'district', 'district_name',
            'title', 'key', 'has_boundary', 'boundary_data',
            'tasks_count', 'tasks',
        ]

    def get_has_boundary(self, obj):
        return obj.boundary_data is not None and bool(obj.boundary_data)
