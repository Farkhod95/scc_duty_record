from django.contrib import admin

from monitoring.models import (
    MainDuty, Task, TaskAssignment, DutyFile, DailyDutyOfficer,
    DutyDay, DutySection, DutySectionAssignment,
    Event, EventAssignment,
    Incident112, Incident112Notification, AlarmLog, TerritoryExitLog,
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
    filter_horizontal = ('employees', 'transports')
    fields = ('employees', 'location', 'transports', 'note')


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


# ── 112 Hodisalar ─────────────────────────────────────────────────────────────

class Incident112NotificationInline(admin.TabularInline):
    model = Incident112Notification
    extra = 0
    readonly_fields = ('employee', 'distance_km', 'sent_at', 'is_read', 'read_at')
    can_delete = False


@admin.register(Incident112)
class Incident112Admin(admin.ModelAdmin):
    list_display = (
        'id', 'card_number', 'dt_create', 'called_phone',
        'incident_type_id', 'priority_id', 'latitude', 'longitude', 'created_time',
    )
    list_filter = ('incident_type_id', 'priority_id', 'new_card', 'created_time')
    search_fields = ('card_number', 'called_phone', 'incident_description', 'note')
    readonly_fields = ('created_time', 'updated_time', 'raw_payload')
    inlines = [Incident112NotificationInline]


@admin.register(AlarmLog)
class AlarmLogAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'duty_section', 'employee', 'alarm_type',
        'point_id', 'paligon_id', 'plate_number', 'received_at',
    )
    list_filter = ('alarm_type', 'received_at')
    search_fields = ('pinfl_hash', 'plate_number', 'message')
    readonly_fields = ('received_at',)


@admin.register(TerritoryExitLog)
class TerritoryExitLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'employee', 'duty_section_assignment', 'exit_time', 'return_time')
    list_filter = ('exit_time',)
    search_fields = ('employee__first_name', 'employee__last_name', 'reason')
