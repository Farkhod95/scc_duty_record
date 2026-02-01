from django.contrib import admin

from django.contrib.contenttypes.models import ContentType
from restapp.models import TranslationTerm, ExtendedContentType, ModelAudit, Notification, ModelChangeLog


class BaseAdmin(admin.ModelAdmin):
    def save_model(self, request, instance, form, change):
        if instance.id is None:
            instance.created_by_id = request.user.id
        instance.updated_by_id = request.user.id
        instance.save()


@admin.register(TranslationTerm)
class UILanguageAdmin(BaseAdmin):
    list_display = ('id', 'term_name', 'name_uz', 'name_uz_cyrl', 'name_ru', 'name_kaa')
    fields = ('term_name', 'name_uz', 'name_uz_cyrl', 'name_ru', 'name_kaa')
    search_fields = ('term_name', 'name_uz', 'name_uz_cyrl', 'name_ru', 'name_kaa')


class ExtendedContentTypeInline(admin.TabularInline):
    model = ExtendedContentType


@admin.register(ContentType)
class ContentType(BaseAdmin):
    ordering = ['app_label']
    list_display = ('id', 'app_label', 'model', 'extend_name')
    fields = ('app_label', 'model')
    inlines = [ExtendedContentTypeInline, ]

    def extend_name(self, instance):
        return instance.extendedcontenttype.extend_name


@admin.register(ModelAudit)
class ModelAuditAdmin(BaseAdmin):
    list_display = ('id', 'user', 'module', 'instance', 'instance_id', 'field_name', 'old_value', 'new_value', 'data', 'action', 'timestamp')
    fields = ('user', 'module', 'instance', 'instance_id', 'field_name', 'old_value', 'new_value', 'data', 'action', 'timestamp')
    search_fields = ('user', 'module', 'instance',)

@admin.register(Notification)
class NotificationAdmin(BaseAdmin):
    list_display = ('id', 'title', 'text', 'status', 'created_time', 'updated_time', 'responsible_by', 'updated_by')
    fields = ('title', 'text', 'status', 'created_time', 'updated_time', 'responsible_by', 'updated_by')
    search_fields = ('status', 'responsible_by',)


@admin.register(ModelChangeLog)
class ModelChangeLogAdmin(BaseAdmin):
    list_display = ('id', 'app_label', 'model_name', 'object_id', 'action', 'user', 'data_before', 'data_after', 'created_at')
    fields = ('app_label', 'model_name', 'object_id', 'action', 'user', 'data_before', 'data_after', 'created_at')
    search_fields = ('app_label', 'action', 'created_at',)
