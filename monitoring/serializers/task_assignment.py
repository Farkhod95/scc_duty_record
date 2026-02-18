from rest_framework import serializers

from monitoring.models import TaskAssignment, AbsenceRequest, AbsenceRequestStatus


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

        main_duty = task.main_duty

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


class AbsenceRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = AbsenceRequest
        fields = ['id', 'task_assignment', 'reason', 'file', 'status',
                  'replacement_employee', 'reviewed_by', 'reviewed_at',
                  'review_note', 'created_time']
        read_only_fields = ['id', 'status', 'replacement_employee', 'reviewed_by',
                            'reviewed_at', 'review_note', 'created_time']


class AbsenceRequestReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = AbsenceRequest
        fields = ['status', 'replacement_employee', 'review_note']

    def validate_status(self, value):
        if value not in [AbsenceRequestStatus.APPROVED, AbsenceRequestStatus.REJECTED]:
            raise serializers.ValidationError("Status APPROVED yoki REJECTED bo'lishi kerak.")
        return value

    def validate(self, attrs):
        instance = self.instance
        if instance and instance.status != AbsenceRequestStatus.PENDING:
            raise serializers.ValidationError("Faqat PENDING holatdagi so'rovni ko'rib chiqish mumkin.")
        replacement = attrs.get('replacement_employee')
        if replacement:
            task_assignment = instance.task_assignment
            main_duty = task_assignment.task.main_duty
            if replacement.organization_id != main_duty.organization_id:
                raise serializers.ValidationError(
                    "O'rinbosar xodim navbatchilik tashkilotiga tegishli bo'lishi kerak."
                )
        return attrs
