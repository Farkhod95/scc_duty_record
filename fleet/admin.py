from django.contrib import admin
from .models import TransportType, Transport


@admin.register(TransportType)
class TransportTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_time']
    search_fields = ['name']


@admin.register(Transport)
class TransportAdmin(admin.ModelAdmin):
    list_display = ['id', 'type', 'name_or_code', 'plate_number', 'capacity', 'organization', 'created_at']
    list_filter = ['type', 'created_at']
    search_fields = ['name_or_code', 'plate_number', 'number', 'model', 'organization__name']
    date_hierarchy = 'created_at'
    autocomplete_fields = ['organization']
