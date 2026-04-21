from django.utils import timezone
from rest_framework import serializers

from monitoring.models import TerritoryExitLog, DutySectionAssignment


class TerritoryExitLogCreateSerializer(serializers.Serializer):
    duty_section_assignment_id = serializers.IntegerField(
        required=False, allow_null=True,
        help_text="DutySectionAssignment ID (ixtiyoriy)"
    )
    reason = serializers.CharField(
        help_text="Hududni tark etish sababi"
    )
    exit_time = serializers.DateTimeField(
        required=False, allow_null=True,
        help_text="Chiqish vaqti ISO 8601 (bo'sh qolsa hozirgi vaqt)"
    )

    def validate_duty_section_assignment_id(self, value):
        if value is None:
            return value
        if not DutySectionAssignment.objects.filter(id=value).exists():
            raise serializers.ValidationError(f"duty_section_assignment_id={value} topilmadi.")
        return value

    def save(self, **kwargs):
        employee = self.context['request'].user
        data = self.validated_data
        return TerritoryExitLog.objects.create(
            employee=employee,
            duty_section_assignment_id=data.get('duty_section_assignment_id'),
            reason=data['reason'],
            exit_time=data.get('exit_time') or timezone.now(),
        )


class TerritoryExitLogReturnSerializer(serializers.Serializer):
    return_time = serializers.DateTimeField(
        required=False, allow_null=True,
        help_text="Qaytish vaqti ISO 8601 (bo'sh qolsa hozirgi vaqt)"
    )


class TerritoryExitLogSerializer(serializers.ModelSerializer):
    employee_id = serializers.IntegerField(source='employee.id')
    employee_name = serializers.SerializerMethodField()
    employee_position = serializers.SerializerMethodField()
    duty_section_assignment_id = serializers.IntegerField(allow_null=True)

    class Meta:
        model = TerritoryExitLog
        fields = [
            'id', 'employee_id', 'employee_name', 'employee_position',
            'duty_section_assignment_id', 'reason',
            'exit_time', 'return_time', 'created_time',
        ]

    def get_employee_name(self, obj):
        return obj.employee.get_full_name()

    def get_employee_position(self, obj):
        if obj.employee.position:
            return obj.employee.position.name
        return None
