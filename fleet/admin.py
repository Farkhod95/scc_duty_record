from django.contrib import admin
from .models import TransportType, Transport


@admin.register(TransportType)
class TransportTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_time']
    search_fields = ['name']


@admin.register(Transport)
class TransportAdmin(admin.ModelAdmin):
    list_display = ['number', 'model', 'type', 'organization', 'created_at']
    list_filter = ['type', 'created_at']
    search_fields = ['number', 'model', 'organization__name']
    date_hierarchy = 'created_at'
    autocomplete_fields = ['organization']