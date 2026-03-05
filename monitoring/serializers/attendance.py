import base64
import binascii
import uuid

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from rest_framework import serializers

from monitoring.models import EmployeeAttendance, AttendanceStatus, Task

User = get_user_model()


class EmployeeAttendanceSerializer(serializers.Serializer):
    pinfl = serializers.CharField(
        help_text="Xodim PINFL ning SHA256 xeshi (64 hex belgisi)"
    )
    status = serializers.ChoiceField(
        choices=AttendanceStatus.choices,
        help_text="ARRIVED — keldi, LEFT — ketdi"
    )
    task_id = serializers.IntegerField(help_text="Vazifa ID raqami")
    datetime = serializers.DateTimeField(help_text="Hodisa vaqti (ISO 8601)")
    location = serializers.DictField(
        child=serializers.FloatField(),
        required=False,
        allow_null=True,
        help_text='GPS: {"lat": 41.123, "lon": 69.456}'
    )
    photo = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=True,
        help_text="Xodim rasmi (base64 formatida, masalan: data:image/jpeg;base64,... yoki sof base64)"
    )

    def validate_pinfl(self, value):
        if len(value) != 64:
            raise serializers.ValidationError(
                "pinfl SHA256 xesh bo'lishi kerak (64 belgi)."
            )
        value = value.lower()
        if not User.objects.filter(pinfl_hash=value).exists():
            raise serializers.ValidationError(
                "Ushbu PINFL bazada topilmadi."
            )
        return value

    def validate_task_id(self, value):
        if not Task.objects.filter(id=value).exists():
            raise serializers.ValidationError(f"task_id={value} topilmadi.")
        return value

    def validate_photo(self, value):
        if not value:
            return None
        # Strip data URI prefix if present (e.g. "data:image/jpeg;base64,...")
        if ',' in value:
            value = value.split(',', 1)[1]
        try:
            base64.b64decode(value, validate=True)
        except (binascii.Error, ValueError):
            raise serializers.ValidationError("photo to'g'ri base64 formatda emas.")
        return value

    def save(self, **kwargs):
        data = self.validated_data
        pinfl_hash = data['pinfl']
        employee = User.objects.get(pinfl_hash=pinfl_hash)

        photo_file = None
        raw_b64 = data.get('photo')
        if raw_b64:
            image_data = base64.b64decode(raw_b64)
            photo_file = ContentFile(image_data, name=f"{uuid.uuid4().hex}.jpg")

        return EmployeeAttendance.objects.create(
            task_id=data['task_id'],
            employee=employee,
            pinfl_hash_received=pinfl_hash,
            is_verified=True,
            status=data['status'],
            event_datetime=data['datetime'],
            location=data.get('location'),
            photo=photo_file,
        )


class EmployeeAttendanceResponseSerializer(serializers.ModelSerializer):
    employee_id = serializers.IntegerField(source='employee.id', allow_null=True)
    employee_name = serializers.SerializerMethodField()
    photo_url = serializers.SerializerMethodField()

    class Meta:
        model = EmployeeAttendance
        fields = [
            'id', 'task_id', 'employee_id', 'employee_name',
            'is_verified', 'status', 'event_datetime', 'location', 'photo_url',
        ]

    def get_employee_name(self, obj):
        return obj.employee.get_full_name() if obj.employee else None

    def get_photo_url(self, obj):
        if not obj.photo:
            return None
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.photo.url)
        return obj.photo.url
