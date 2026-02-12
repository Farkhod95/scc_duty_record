from rest_framework import serializers

from monitoring.models import DutySection, DutySectionType


class DutySectionTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DutySectionType
        fields = [
            'id', 'name', 'organization', 'sort_order',
            'created_time', 'updated_time', 'created_by', 'updated_by',
        ]
        read_only_fields = ['id', 'created_time', 'updated_time', 'created_by', 'updated_by']


class DutySectionTypeListSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source='organization.name', read_only=True)

    class Meta:
        model = DutySectionType
        fields = ['id', 'name', 'organization', 'organization_name', 'sort_order']


class DutySectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DutySection
        fields = [
            'id', 'main_duty', 'section_type', 'name', 'sort_order',
            'created_time', 'updated_time', 'created_by', 'updated_by',
        ]
        read_only_fields = ['id', 'created_time', 'updated_time', 'created_by', 'updated_by']


class DutySectionListSerializer(serializers.ModelSerializer):
    tasks_count = serializers.IntegerField(read_only=True)
    section_type_name = serializers.CharField(source='section_type.name', read_only=True, default=None)

    class Meta:
        model = DutySection
        fields = [
            'id', 'main_duty', 'section_type', 'section_type_name',
            'name', 'sort_order', 'tasks_count', 'created_time',
        ]


class DutySectionDetailSerializer(serializers.ModelSerializer):
    tasks = serializers.SerializerMethodField()
    section_type_name = serializers.CharField(source='section_type.name', read_only=True, default=None)

    class Meta:
        model = DutySection
        fields = [
            'id', 'main_duty', 'section_type', 'section_type_name',
            'name', 'sort_order', 'tasks', 'created_time', 'updated_time',
        ]

    def get_tasks(self, obj):
        from monitoring.serializers.task import TaskDetailSerializer
        return TaskDetailSerializer(obj.tasks.all(), many=True).data
