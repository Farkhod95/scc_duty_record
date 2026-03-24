from django.contrib import admin
from tablet.models import DutyCheckIn, EmployeeLocationLog


@admin.register(DutyCheckIn)
class DutyCheckInAdmin(admin.ModelAdmin):
    list_display = ('employee', 'duty_section', 'check_in_time', 'check_out_time', 'is_active')
    list_filter = ('duty_section__duty_day__organization',)
    search_fields = ('employee__first_name', 'employee__last_name')
    readonly_fields = ('check_in_time', 'check_out_time')

    @admin.display(boolean=True)
    def is_active(self, obj):
        return obj.is_active


@admin.register(EmployeeLocationLog)
class EmployeeLocationLogAdmin(admin.ModelAdmin):
    list_display = ('employee', 'duty_section', 'latitude', 'longitude', 'accuracy', 'timestamp')
    list_filter = ('duty_section__duty_day__organization',)
    search_fields = ('employee__first_name', 'employee__last_name')
    readonly_fields = ('timestamp',)
