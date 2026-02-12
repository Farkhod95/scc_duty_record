from rest_framework import serializers

from monitoring.models import DutySection


class DutySectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DutySection
        fields = [
            'id', 'main_duty', 'name', 'sort_order',
            'created_time', 'updated_time', 'created_by', 'updated_by',
        ]
        read_only_fields = ['id', 'created_time', 'updated_time', 'created_by', 'updated_by']


class DutySectionListSerializer(serializers.ModelSerializer):
    tasks_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = DutySection
        fields = [
            'id', 'main_duty', 'name', 'sort_order',
            'tasks_count', 'created_time',
        ]


class DutySectionDetailSerializer(serializers.ModelSerializer):
    tasks = serializers.SerializerMethodField()

    class Meta:
        model = DutySection
        fields = [
            'id', 'main_duty', 'name', 'sort_order',
            'tasks', 'created_time', 'updated_time',
        ]

    def get_tasks(self, obj):
        from monitoring.serializers.task import TaskDetailSerializer
        return TaskDetailSerializer(obj.tasks.all(), many=True).data
