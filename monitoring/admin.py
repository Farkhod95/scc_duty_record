from django.contrib import admin

from monitoring.models import (
    MainDuty, Task, TaskAssignment, DutyFile, DailyDutyOfficer,
    DutyDay, DutySection, DutySectionAssignment,
    Event, EventAssignment,
)


# ── Eski modellar ────────────────────────────────────────────────────────────

@admin.register(MainDuty)
class MainDutyAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'organization', 'status', 'duty_date', 'start_time', 'end_time')
    list_filter = ('status', 'duty_date', 'organization')
    search_fields = ('title', 'organization__name')
    readonly_fields = ('created_time', 'updated_time', 'created_by', 'updated_by', 'approved_at')


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'main_duty', 'task_type', 'start_time', 'end_time')
    list_filter = ('task_type',)
    search_fields = ('title',)


@admin.register(TaskAssignment)
class TaskAssignmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'task', 'employee', 'transport')
    search_fields = ('employee__first_name', 'employee__last_name', 'task__title')


@admin.register(DutyFile)
class DutyFileAdmin(admin.ModelAdmin):
    list_display = ('id', 'main_duty', 'name', 'file', 'created_time')
    search_fields = ('name',)


@admin.register(DailyDutyOfficer)
class DailyDutyOfficerAdmin(admin.ModelAdmin):
    list_display = ('id', 'organization', 'officer', 'duty_date', 'assigned_by')
    list_filter = ('duty_date', 'organization')
    search_fields = ('officer__first_name', 'officer__last_name')


# ── Yangi navbatchilik (DutyDay) ─────────────────────────────────────────────

class DutySectionAssignmentInline(admin.StackedInline):
    model = DutySectionAssignment
    extra = 0
    filter_horizontal = ('employees', 'mahallas', 'transports')
    fields = ('employees', 'mahallas', 'transports', 'note')


class DutySectionInline(admin.TabularInline):
    model = DutySection
    extra = 0
    fields = ('stage_number', 'name', 'start_time', 'end_time')
    readonly_fields = ('stage_number',)
    show_change_link = True


@admin.register(DutySection)
class DutySectionAdmin(admin.ModelAdmin):
    list_display = ('id', 'duty_day', 'stage_number', 'name', 'start_time', 'end_time')
    list_filter = ('duty_day__organization',)
    search_fields = ('name', 'duty_day__organization__name')
    readonly_fields = ('stage_number',)
    inlines = [DutySectionAssignmentInline]


@admin.register(DutyDay)
class DutyDayAdmin(admin.ModelAdmin):
    list_display = ('id', 'organization', 'duty_date', 'status', 'submitted_by', 'approved_by')
    list_filter = ('status', 'duty_date', 'organization')
    search_fields = ('organization__name',)
    readonly_fields = (
        'submitted_at', 'submitted_by',
        'collected_at', 'collected_by',
        'approved_at', 'approved_by',
        'rejected_at', 'rejected_by', 'rejection_reason', 'rejected_at_stage',
        'created_time', 'updated_time', 'created_by', 'updated_by',
    )
    inlines = [DutySectionInline]
    autocomplete_fields = ('organization',)
    list_select_related = ('organization', 'submitted_by', 'approved_by')


# ── Tadbir (Event) ────────────────────────────────────────────────────────────

class EventAssignmentInline(admin.StackedInline):
    model = EventAssignment
    extra = 0
    filter_horizontal = ('employees', 'mahallas', 'transports')
    fields = ('employees', 'mahallas', 'transports', 'note')


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'organization', 'event_date', 'status', 'submitted_by', 'approved_by')
    list_filter = ('status', 'event_date', 'organization')
    search_fields = ('title', 'organization__name')
    readonly_fields = (
        'submitted_at', 'submitted_by',
        'collected_at', 'collected_by',
        'approved_at', 'approved_by',
        'rejected_at', 'rejected_by', 'rejection_reason', 'rejected_at_stage',
        'created_time', 'updated_time', 'created_by', 'updated_by',
    )
    inlines = [EventAssignmentInline]
    autocomplete_fields = ('organization',)
    list_select_related = ('organization', 'submitted_by', 'approved_by')
