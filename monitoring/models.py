from django.db import models
from django.utils.translation import gettext_lazy as _
from restapp.models import BaseModel
from django.contrib.auth import get_user_model

User = get_user_model()


class DutyStatus(models.TextChoices):
    PENDING = 'pending', _('Pending')
    APPROVED = 'approved', _('Approved')
    REJECTED = 'rejected', _('Rejected')
    ACTIVE = 'active', _('Active')
    COMPLETED = 'completed', _('Completed')
    CANCELLED = 'cancelled', _('Cancelled')

class ChangeRequestStatus(models.TextChoices):
    PENDING = 'pending', _('Pending')
    APPROVED = 'approved', _('Approved')
    REJECTED = 'rejected', _('Rejected')

class DutyUserStatus(models.TextChoices):
    ON_DUTY = 'on_duty', _('On duty')
    BREAK = 'break', _('Break')
    SOS = 'sos', _('SOS')
    OFFLINE = 'offline', _('Offline')


class Duty(BaseModel):
    organization = models.ForeignKey('directory.Organization', on_delete=models.CASCADE, related_name='duties', help_text=_("Navbatchilik tegishli tashkilot"))
    mahalla = models.ForeignKey('directory.Mahalla', on_delete=models.CASCADE, related_name='duties', null=True, blank=True, help_text=_("Navbatchilik tegishli mahalla"))
    name = models.CharField(_('Name'), max_length=255, help_text=_("Navbatchilik nomi"))
    start_time = models.DateTimeField(_('Start time'), help_text=_("Boshlanish vaqti"))
    end_time = models.DateTimeField(_('End time'), help_text=_("Tugash vaqti"))
    status = models.CharField(_('Status'), max_length=20, choices=DutyStatus.choices, default=DutyStatus.PENDING, help_text=_("Navbatchilik holati"))
    file = models.FileField(_('File'), upload_to='duties/%Y/%m/%d/', null=True, blank=True, help_text=_("Biriktirilgan fayl"))
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_duties', help_text=_("Kim tasdiqladi"))
    approved_at = models.DateTimeField(_('Approved at'), null=True, blank=True, help_text=_("Tasdiqlangan vaqt"))
    rejection_reason = models.TextField(_('Rejection reason'), null=True, blank=True, help_text=_("Agar status rejected bo'lsa, sababi"))

    class Meta:
        verbose_name = _("Duty")
        verbose_name_plural = _("Duties")
        ordering = ['-start_time']
        indexes = [
            models.Index(fields=['organization', 'status']),
            models.Index(fields=['start_time', 'end_time']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.name} - {self.get_status_display()}"

    def is_active(self):
        from django.utils import timezone
        now = timezone.now()
        return self.start_time <= now <= self.end_time and self.status in [DutyStatus.ACTIVE, DutyStatus.APPROVED]


class DutyChangeRequest(BaseModel):
    duty = models.ForeignKey(Duty, on_delete=models.CASCADE, related_name='change_requests', help_text=_("Qaysi navbatchilik uchun"))
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='requested_duty_changes', help_text=_("Kim so'rov yubordi"))
    old_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='old_duty_assignments', help_text=_("Eski user (almashtirilayotgan)"))
    new_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='new_duty_assignments', help_text=_("Yangi user (o'rniga keluvchi)"))
    reason = models.TextField(_('Reason'),help_text=_("Almashtirish sababi"))
    attachment_file = models.FileField(_('Attachment'), upload_to='duty_change_requests/%Y/%m/%d/', null=True, blank=True, help_text=_("Qo'shimcha fayl (agar kerak bo'lsa)"))
    status = models.CharField(_('Status'), max_length=20, choices=ChangeRequestStatus.choices, default=ChangeRequestStatus.PENDING, help_text=_("So'rov holati"))
    response_note = models.TextField(_('Response note'), null=True, blank=True, help_text=_("Javob yoki izoh"))
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='processed_duty_changes', help_text=_("Kim ko'rib chiqdi"))
    processed_at = models.DateTimeField(_('Processed at'), null=True, blank=True, help_text=_("Ko'rib chiqilgan vaqt"))

    class Meta:
        verbose_name = _("Duty change request")
        verbose_name_plural = _("Duty change requests")
        ordering = ['-created_time']
        indexes = [
            models.Index(fields=['duty', 'status']),
            models.Index(fields=['requested_by', 'status']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"So'rov #{self.id} - {self.duty.name} ({self.get_status_display()})"

    def approve(self, processed_by, note=None):
        from django.utils import timezone
        self.status = ChangeRequestStatus.APPROVED
        self.processed_by = processed_by
        self.processed_at = timezone.now()
        if note:
            self.response_note = note
        self.save()

    def reject(self, processed_by, note):
        from django.utils import timezone
        self.status = ChangeRequestStatus.REJECTED
        self.processed_by = processed_by
        self.processed_at = timezone.now()
        self.response_note = note
        self.save()


class DutyUser(BaseModel):
    duty = models.ForeignKey(Duty, on_delete=models.CASCADE, related_name='duty_users', help_text=_("Qaysi navbatchilik"))
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='duty_assignments', help_text=_("Navbatdagi user"))
    transport = models.ForeignKey('fleet.Transport', on_delete=models.SET_NULL, null=True, blank=True, related_name='duty_users', help_text=_("Shu navbatda qaysi transportda?"))
    # type = models.ForeignKey('DutyType', on_delete=models.SET_NULL, null=True, blank=True, related_name='duty_users', help_text=_("Navbat turi"))
    is_driver = models.BooleanField(_('Is driver'), default=False, help_text=_("Haydovchimi?"))

    # Notifications
    is_notified = models.BooleanField(_('Is notified'), default=False, help_text=_("Xabarnoma yuborilganmi?"))
    notified_at = models.DateTimeField(_('Notified at'), null=True, blank=True, help_text=_("Xabarnoma yuborilgan vaqt"))

    # Check-in
    check_in_time = models.DateTimeField(_('Check in time'), null=True, blank=True, help_text=_("Kelgan vaqti"))
    check_in_photo = models.ImageField(_('Check in photo'), upload_to='duty_checkin/%Y/%m/%d/', null=True, blank=True, help_text=_("Kelganda tushirilgan foto"))
    check_in_lat = models.FloatField(_('Check in latitude'), null=True, blank=True, help_text=_("Kelgan joy latitude"))
    check_in_lon = models.FloatField(_('Check in longitude'), null=True, blank=True, help_text=_("Kelgan joy longitude")
    )
    check_in_verified = models.BooleanField(_('Check in verified'), default=False, help_text=_("Check-in tasdiqlangan")
    )

    # Check-out
    check_out_time = models.DateTimeField(_('Check out time'), null=True, blank=True, help_text=_("Ketgan vaqti"))
    check_out_lat = models.FloatField(_('Check out latitude'), null=True, blank=True, help_text=_("Ketgan joy latitude"))
    check_out_lon = models.FloatField(_('Check out longitude'), null=True, blank=True, help_text=_("Ketgan joy longitude"))

    # Current status
    current_status = models.CharField(_('Current status'), max_length=20, choices=DutyUserStatus.choices, default=DutyUserStatus.OFFLINE, help_text=_("Hozirgi holat"))

    class Meta:
        verbose_name = _("Duty user")
        verbose_name_plural = _("Duty users")
        ordering = ['-created_time']
        unique_together = [['duty', 'user']]
        indexes = [
            models.Index(fields=['duty', 'user']),
            models.Index(fields=['current_status']),
            models.Index(fields=['check_in_time']),
        ]

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.duty.name}"

    def check_in(self, lat=None, lon=None, photo=None):
        from django.utils import timezone
        self.check_in_time = timezone.now()
        self.check_in_lat = lat
        self.check_in_lon = lon
        if photo:
            self.check_in_photo = photo
        self.current_status = DutyUserStatus.ON_DUTY
        self.save()

    def check_out(self, lat=None, lon=None):
        from django.utils import timezone
        self.check_out_time = timezone.now()
        self.check_out_lat = lat
        self.check_out_lon = lon
        self.current_status = DutyUserStatus.OFFLINE
        self.save()