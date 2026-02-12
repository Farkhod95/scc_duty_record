from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import MainDuty, DutySection, Task, TaskAssignment, DutyFile, DailyDutyOfficer


@admin.register(MainDuty)
class MainDutyAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'organization', 'status', 'duty_date', 'start_time', 'end_time']
    list_filter = ['status', 'duty_date', 'organization']
    search_fields = ['title', 'organization__name']
    readonly_fields = ['created_time', 'updated_time', 'created_by', 'updated_by', 'approved_at']


@admin.register(DutySection)
class DutySectionAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'main_duty', 'sort_order']
    list_filter = ['main_duty']
    search_fields = ['name']


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'duty_section', 'task_type', 'start_time', 'end_time']
    list_filter = ['task_type']
    search_fields = ['title']


@admin.register(TaskAssignment)
class TaskAssignmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'task', 'employee', 'transport', 'role_in_transport']
    list_filter = ['role_in_transport']
    search_fields = ['employee__first_name', 'employee__last_name', 'task__title']


@admin.register(DutyFile)
class DutyFileAdmin(admin.ModelAdmin):
    list_display = ['id', 'main_duty', 'name', 'file', 'created_time']
    search_fields = ['name']


@admin.register(DailyDutyOfficer)
class DailyDutyOfficerAdmin(admin.ModelAdmin):
    list_display = ['id', 'organization', 'officer', 'duty_date', 'assigned_by']
    list_filter = ['duty_date', 'organization']
    search_fields = ['officer__first_name', 'officer__last_name']
