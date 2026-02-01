from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.utils import timezone
from .models import Duty, DutyChangeRequest, DutyStatus, ChangeRequestStatus


@admin.register(Duty)
class DutyAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'name', 'organization', 'mahalla', 'status_badge',
        'start_time', 'end_time', 'is_active_badge', 'created_time'
    ]
    list_filter = ['status', 'start_time', 'end_time', 'organization', 'created_time']
    search_fields = ['name', 'organization__name', 'mahalla__name']
    readonly_fields = ['created_time', 'updated_time', 'created_by', 'updated_by', 'approved_at']
    date_hierarchy = 'start_time'

    fieldsets = (
        (_('Asosiy ma\'lumotlar'), {
            'fields': ('name', 'organization', 'mahalla', 'status')
        }),
        (_('Vaqt'), {
            'fields': ('start_time', 'end_time')
        }),
        (_('Fayl'), {
            'fields': ('file',)
        }),
        (_('Tasdiqlash'), {
            'fields': ('approved_by', 'approved_at', 'rejection_reason'),
            'classes': ('collapse',)
        }),
        (_('Sistema ma\'lumotlari'), {
            'fields': ('created_time', 'updated_time', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )

    def status_badge(self, obj):
        colors = {
            DutyStatus.PENDING: 'orange',
            DutyStatus.APPROVED: 'green',
            DutyStatus.REJECTED: 'red',
            DutyStatus.ACTIVE: 'blue',
            DutyStatus.COMPLETED: 'gray',
            DutyStatus.CANCELLED: 'darkred',
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )

    status_badge.short_description = _('Status')

    def is_active_badge(self, obj):
        if obj.is_active():
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Faol</span>'
            )
        return format_html('<span style="color: gray;">—</span>')

    is_active_badge.short_description = _('Hozir faolmi?')

    def save_model(self, request, obj, form, change):
        if not change:  # yangi yaratilayotgan bo'lsa
            obj.created_by = request.user
        obj.updated_by = request.user

        # Agar status approved bo'lsa va approved_at bo'sh bo'lsa
        if obj.status == DutyStatus.APPROVED and not obj.approved_at:
            obj.approved_at = timezone.now()
            obj.approved_by = request.user

        super().save_model(request, obj, form, change)

    actions = ['approve_duties', 'reject_duties', 'activate_duties']

    def approve_duties(self, request, queryset):
        count = 0
        for duty in queryset:
            if duty.status == DutyStatus.PENDING:
                duty.status = DutyStatus.APPROVED
                duty.approved_by = request.user
                duty.approved_at = timezone.now()
                duty.save()
                count += 1
        self.message_user(request, _(f'{count} ta navbatchilik tasdiqlandi'))

    approve_duties.short_description = _('Tanlangan navbatchilikni tasdiqlash')

    def reject_duties(self, request, queryset):
        count = queryset.filter(status=DutyStatus.PENDING).update(status=DutyStatus.REJECTED)
        self.message_user(request, _(f'{count} ta navbatchilik rad etildi'))

    reject_duties.short_description = _('Tanlangan navbatchilikni rad etish')

    def activate_duties(self, request, queryset):
        count = queryset.filter(status=DutyStatus.APPROVED).update(status=DutyStatus.ACTIVE)
        self.message_user(request, _(f'{count} ta navbatchilik faollashtirildi'))

    activate_duties.short_description = _('Tanlangan navbatchilikni faollashtirish')


@admin.register(DutyChangeRequest)
class DutyChangeRequestAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'duty', 'requested_by', 'old_user', 'new_user',
        'status_badge', 'processed_by', 'created_time'
    ]
    list_filter = ['status', 'created_time', 'processed_at']
    search_fields = [
        'duty__name', 'requested_by__username',
        'old_user__username', 'new_user__username', 'reason'
    ]
    readonly_fields = [
        'created_time', 'updated_time', 'created_by',
        'updated_by', 'processed_at'
    ]
    date_hierarchy = 'created_time'
    autocomplete_fields = ['duty', 'requested_by', 'old_user', 'new_user', 'processed_by']

    fieldsets = (
        (_('So\'rov ma\'lumotlari'), {
            'fields': ('duty', 'requested_by', 'reason', 'attachment_file')
        }),
        (_('Almashtirish'), {
            'fields': ('old_user', 'new_user')
        }),
        (_('Javob'), {
            'fields': ('status', 'response_note', 'processed_by', 'processed_at'),
            'classes': ('collapse',)
        }),
        (_('Sistema ma\'lumotlari'), {
            'fields': ('created_time', 'updated_time', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )

    def status_badge(self, obj):
        colors = {
            ChangeRequestStatus.PENDING: 'orange',
            ChangeRequestStatus.APPROVED: 'green',
            ChangeRequestStatus.REJECTED: 'red',
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )

    status_badge.short_description = _('Status')

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user

        if 'status' in form.changed_data and obj.status != ChangeRequestStatus.PENDING:
            if not obj.processed_at:
                obj.processed_at = timezone.now()
                obj.processed_by = request.user

        super().save_model(request, obj, form, change)

    actions = ['approve_requests', 'reject_requests']

    def approve_requests(self, request, queryset):
        count = 0
        for req in queryset.filter(status=ChangeRequestStatus.PENDING):
            req.approve(request.user, note=_('Admin tomonidan tasdiqlandi'))
            count += 1
        self.message_user(request, _(f'{count} ta so\'rov tasdiqlandi'))

    approve_requests.short_description = _('Tanlangan so\'rovlarni tasdiqlash')

    def reject_requests(self, request, queryset):
        count = 0
        for req in queryset.filter(status=ChangeRequestStatus.PENDING):
            req.reject(request.user, note=_('Admin tomonidan rad etildi'))
            count += 1
        self.message_user(request, _(f'{count} ta so\'rov rad etildi'))

    reject_requests.short_description = _('Tanlangan so\'rovlarni rad etish')