from django.conf import settings
from django.db import models
from django.contrib.contenttypes.models import ContentType

from django.utils.translation import gettext_lazy as _

User = settings.AUTH_USER_MODEL


class BaseModel(models.Model):
    created_time = models.DateTimeField(auto_now_add=True, help_text=_("Yaratilgan vaqt"))
    updated_time = models.DateTimeField(auto_now=True, help_text=_("O'zgartirilgan vaqt"))
    created_by = models.ForeignKey(User, related_name='created_%(model_name)s', null=True, on_delete=models.SET_NULL, help_text=_("Kim yaratdi (User bilan bog'lanadi)"))
    updated_by = models.ForeignKey(User, related_name='updated_%(model_name)s', null=True, on_delete=models.SET_NULL, help_text=_("Kim o'zgartirdi (User bilan bog'lanadi)"))

    class Meta:
        abstract = True
        ordering = ('id',)
        get_latest_by = 'created_time'


class TranslationTerm(BaseModel):
    term_name = models.CharField(_('Term name'), max_length=500, blank=False, null=False)
    name = models.CharField(_('Name'), max_length=500, blank=False, null=False)


class ModelAudit(models.Model):
    user = models.ForeignKey(User, related_name='audit_user', null=True, on_delete=models.SET_NULL)
    module = models.CharField(max_length=255, null=True, blank=True)
    instance = models.CharField(max_length=255, null=True, blank=True)
    instance_id = models.BigIntegerField(null=True, blank=True)
    field_name = models.TextField(null=True, blank=True)
    old_value = models.TextField(null=True, blank=True)
    new_value = models.TextField(null=True, blank=True)
    data = models.TextField(null=True, blank=True)
    action = models.CharField(max_length=16, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)


class ExtendedContentType(models.Model):
    extend_name = models.CharField(_('Extended name'), max_length=100, null=True, blank=True)
    content_type = models.OneToOneField(ContentType, on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(_('Active'), default=False, null=True, blank=True)

    def __str__(self):
        return self.extend_name


class Notification(models.Model):
    class STATUS(models.TextChoices):
        UNREAD = 'unread', _('Unread')  # Unread
        READ = 'read', _('Read')  # Read

    title = models.CharField(_('Title'), max_length=255, null=True, blank=True,
                            help_text=_("Sarlavha"))
    text = models.TextField(_('Text'), null=True, blank=True, help_text=_("Text"))
    status = models.CharField(choices=STATUS.choices, default='unread', max_length=6, null=True, blank=True, help_text=_("Holati"))
    created_time = models.DateTimeField(auto_now_add=True, help_text=_("Yaratilgan vaqt"))
    updated_time = models.DateTimeField(auto_now=True, help_text=_("Yangilangan vaqt"))
    responsible_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='created_by_notif', null=True,
                                   on_delete=models.SET_NULL, help_text=_("Yaratgan foydalanuvchi"))
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='updated_by_notif', null=True,
                                   on_delete=models.SET_NULL, help_text=_("Yangilagan foydalanuvchi"))

    class Meta:
        verbose_name = _('Notification')
        verbose_name_plural = _('Notifications')
        indexes = [
            models.Index(fields=['responsible_by']),
            models.Index(fields=['updated_by']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return self.title


class ModelChangeLog(models.Model):
    class ActionChoices(models.TextChoices):
        CREATE = 'create', _('Create')
        UPDATE = 'update', _('Update')
        DELETE = 'delete', _('Delete')
        LOGIN = 'login', _('Login')
        LOGOUT = 'logout', _('Logout')
        VIEW = 'view', _('View')
        SEARCH = 'search', _('Search')

    app_label  = models.CharField(max_length=100, help_text=_("App label (masalan: 'monitoring')"))
    model_name = models.CharField(max_length=100, help_text=_("Model nomi (masalan: 'Teenager')"))
    object_id  = models.CharField(max_length=64, help_text=_("Obyekt PK (string ko‘rinishda)"))
    action     = models.CharField(max_length=10, choices=ActionChoices.choices, help_text=_("Amal turi: create / update / delete"))
    user       = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                                   related_name='model_change_logs', help_text=_("O‘zgarishni qilgan foydalanuvchi (agar mavjud bo‘lsa)"))
    data_before = models.JSONField(null=True, blank=True, help_text=_("O‘zgarishdan OLDINGI ma'lumotlar snapshot (JSON)"))
    data_after  = models.JSONField(null=True, blank=True, help_text=_("O‘zgarishdan KEYINGI ma'lumotlar snapshot (JSON)"))
    created_at  = models.DateTimeField(auto_now_add=True, help_text=_("Log yozilgan vaqt"))

    class Meta:
        verbose_name = _("Model change log")
        verbose_name_plural = _("Model change logs")
        indexes = [
            models.Index(fields=["app_label", "model_name"]),
            models.Index(fields=["object_id"]),
            models.Index(fields=["action"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["user"]),
        ]

    def __str__(self):
        return f"[{self.action}] {self.app_label}.{self.model_name} ({self.object_id})"