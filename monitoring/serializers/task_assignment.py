from rest_framework import serializers

from monitoring.models import TaskAssignment


class TaskAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskAssignment
        fields = [
            'id', 'task', 'employee', 'transport', 'role_in_transport', 'note',
            'created_time', 'updated_time', 'created_by', 'updated_by',
        ]
        read_only_fields = ['id', 'created_time', 'updated_time', 'created_by', 'updated_by']

    def validate(self, attrs):
        task = attrs.get('task') or self.instance.task
        employee = attrs.get('employee') or self.instance.employee
        transport = attrs.get('transport', self.instance.transport if self.instance else None)

        main_duty = task.duty_section.main_duty

        if employee.organization_id != main_duty.organization_id:
            raise serializers.ValidationError({
                'employee': "Xodim navbatchilik tashkilotiga tegishli bo'lishi kerak."
            })

        if transport and transport.organization_id != main_duty.organization_id:
            raise serializers.ValidationError({
                'transport': "Transport navbatchilik tashkilotiga tegishli bo'lishi kerak."
            })

        return attrs


class TaskAssignmentListSerializer(serializers.ModelSerializer):
    employee_full_name = serializers.SerializerMethodField()
    transport_info = serializers.SerializerMethodField()
    role_display = serializers.CharField(source='get_role_in_transport_display', read_only=True)

    class Meta:
        model = TaskAssignment
        fields = [
            'id', 'task', 'employee', 'employee_full_name',
            'transport', 'transport_info', 'role_in_transport', 'role_display',
            'note', 'created_time',
        ]

    def get_employee_full_name(self, obj):
        if obj.employee:
            return obj.employee.get_full_name()
        return None

    def get_transport_info(self, obj):
        if obj.transport:
            return str(obj.transport)
        return None
