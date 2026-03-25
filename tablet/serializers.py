from django.utils import timezone
from rest_framework import serializers

from monitoring.models import DutySection
from tablet.models import DutyCheckIn


class TabletMeSerializer(serializers.Serializer):
    username = serializers.CharField()
    last_name = serializers.CharField()
    first_name = serializers.CharField()
    second_name = serializers.CharField(allow_null=True)
    full_name = serializers.SerializerMethodField()
    phone_number = serializers.CharField()
    pinfl = serializers.CharField(allow_null=True)
    gender = serializers.CharField(allow_null=True)
    date_of_birthday = serializers.DateField(allow_null=True)
    avatar = serializers.SerializerMethodField()
    special_rank = serializers.CharField(source='special_rank.name', allow_null=True)
    organization = serializers.SerializerMethodField()
    position = serializers.CharField(source='position.name', allow_null=True)
    department = serializers.CharField(source='department.name', allow_null=True)

    def get_full_name(self, obj):
        return ' '.join(p for p in [obj.last_name, obj.first_name, obj.second_name] if p)

    def get_avatar(self, obj):
        if not obj.avatar:
            return None
        request = self.context.get('request')
        return request.build_absolute_uri(obj.avatar.url) if request else obj.avatar.url

    def get_organization(self, obj):
        org = obj.organization
        if not org:
            return None
        return {
            'name': org.name,
            'code': org.code,
            'stages_count': org.stages_count,
            'region': org.region.name if org.region else None,
            'district': org.district.name if org.district else None,
        }



class TabletLocationSerializer(serializers.Serializer):
    """Mavjud location + mahallalar."""
    id = serializers.IntegerField()
    title = serializers.CharField()
    mahallas = serializers.SerializerMethodField()

    def get_mahallas(self, obj):
        return [{'id': m.pk, 'name': m.name} for m in obj.mahallas.all()]


class TabletAssignmentSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    location = TabletLocationSerializer(allow_null=True)
    employees = serializers.SerializerMethodField()
    transports = serializers.SerializerMethodField()
    note = serializers.CharField(allow_null=True)

    def get_employees(self, obj):
        return [{'id': e.pk, 'name': str(e)} for e in obj.employees.all()]

    def get_transports(self, obj):
        return [{'id': t.pk, 'name': str(t)} for t in obj.transports.all()]


class TabletCheckInSerializer(serializers.Serializer):
    is_started = serializers.SerializerMethodField()
    is_finished = serializers.SerializerMethodField()
    check_in_time = serializers.SerializerMethodField()
    check_out_time = serializers.SerializerMethodField()

    def get_is_started(self, obj):
        checkin = self.context.get('checkin')
        return checkin is not None and checkin.check_in_time is not None

    def get_is_finished(self, obj):
        checkin = self.context.get('checkin')
        return checkin is not None and checkin.check_out_time is not None

    def get_check_in_time(self, obj):
        checkin = self.context.get('checkin')
        return checkin.check_in_time if checkin else None

    def get_check_out_time(self, obj):
        checkin = self.context.get('checkin')
        return checkin.check_out_time if checkin else None


class TabletSectionSerializer(serializers.ModelSerializer):
    duty_date = serializers.DateField(source='duty_day.duty_date', read_only=True)
    organization_name = serializers.CharField(source='duty_day.organization.name', read_only=True)
    duty_status = serializers.CharField(source='duty_day.status', read_only=True)
    assignments = TabletAssignmentSerializer(many=True, read_only=True)
    checkin = serializers.SerializerMethodField()

    class Meta:
        model = DutySection
        fields = [
            'id', 'stage_number', 'name', 'start_time', 'end_time',
            'duty_date', 'organization_name', 'duty_status',
            'assignments', 'checkin',
        ]

    def get_checkin(self, obj):
        user = self.context['request'].user
        checkin = next(
            (c for c in obj.checkins.all() if c.employee_id == user.pk),
            None
        )
        return {
            'is_started': checkin is not None and checkin.check_in_time is not None,
            'is_finished': checkin is not None and checkin.check_out_time is not None,
            'check_in_time': checkin.check_in_time if checkin else None,
            'check_out_time': checkin.check_out_time if checkin else None,
        }


class TodayMahallaSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    boundary_data = serializers.JSONField()


class TodayLocationPointSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    order = serializers.IntegerField()
    name = serializers.CharField(allow_null=True)
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6, allow_null=True)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6, allow_null=True)
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()


class TodayLocationSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    boundary_data = serializers.JSONField()
    mahallas = serializers.SerializerMethodField()
    points = serializers.SerializerMethodField()

    def get_mahallas(self, obj):
        return TodayMahallaSerializer(obj.mahallas.all(), many=True).data

    def get_points(self, obj):
        return TodayLocationPointSerializer(obj.points.all(), many=True).data


class TodayAssignmentSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    location = TodayLocationSerializer(allow_null=True)
    employees = serializers.SerializerMethodField()
    transports = serializers.SerializerMethodField()
    note = serializers.CharField(allow_null=True)

    def get_employees(self, obj):
        return [{'id': e.pk, 'name': str(e)} for e in obj.employees.all()]

    def get_transports(self, obj):
        return [{'id': t.pk, 'name': str(t)} for t in obj.transports.all()]


class TodaySectionSerializer(serializers.ModelSerializer):
    duty_date = serializers.DateField(source='duty_day.duty_date', read_only=True)
    organization_name = serializers.CharField(source='duty_day.organization.name', read_only=True)
    duty_status = serializers.CharField(source='duty_day.status', read_only=True)
    assignments = serializers.SerializerMethodField()
    checkin = serializers.SerializerMethodField()

    class Meta:
        model = DutySection
        fields = [
            'id', 'stage_number', 'name', 'start_time', 'end_time',
            'duty_date', 'organization_name', 'duty_status',
            'assignments', 'checkin',
        ]

    def get_assignments(self, obj):
        return TodayAssignmentSerializer(obj.assignments.all(), many=True).data

    def get_checkin(self, obj):
        user = self.context['request'].user
        checkin = next(
            (c for c in obj.checkins.all() if c.employee_id == user.pk),
            None,
        )
        return {
            'is_started': checkin is not None and checkin.check_in_time is not None,
            'is_finished': checkin is not None and checkin.check_out_time is not None,
            'check_in_time': checkin.check_in_time if checkin else None,
            'check_out_time': checkin.check_out_time if checkin else None,
        }


class DutyCheckInSerializer(serializers.ModelSerializer):
    is_active = serializers.BooleanField(read_only=True)
    section_name = serializers.CharField(source='duty_section.name', read_only=True)

    class Meta:
        model = DutyCheckIn
        fields = ['id', 'duty_section', 'section_name', 'check_in_time', 'check_out_time', 'is_active']
        read_only_fields = fields
