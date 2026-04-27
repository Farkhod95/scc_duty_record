from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from restapp.models import BaseModel

User = get_user_model()


class TabletSession(models.Model):
    """
    Har bir user uchun bitta aktiv planshet sessiyasi.
    Yangi login bo'lganda eski sessiya o'chiriladi — eski tokenlar avtomatik yaroqsiz bo'ladi.
    """
    user = models.OneToOneField(
        User, on_delete=models.CASCADE,
        related_name='tablet_session',
    )
    session_key = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Tablet session'
        verbose_name_plural = 'Tablet sessions'

    def __str__(self):
        return f"{self.user} — {self.created_at:%Y-%m-%d %H:%M}"


class DutyCheckIn(BaseModel):
    """Navbatchi boshlash/tugatish vaqtini qayd etadi."""
    employee = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='duty_checkins',
        help_text=_("Navbatchi xodim")
    )
    duty_section = models.ForeignKey(
        'monitoring.DutySection', on_delete=models.CASCADE,
        related_name='checkins',
        help_text=_("Qaysi bosqich")
    )
    check_in_time = models.DateTimeField(
        _('Check-in vaqti'), null=True, blank=True,
        help_text=_("Navbatchilik boshlagan vaqt")
    )
    check_out_time = models.DateTimeField(
        _('Check-out vaqti'), null=True, blank=True,
        help_text=_("Navbatchilik tugatgan vaqt")
    )

    class Meta:
        verbose_name = _('Duty check-in')
        verbose_name_plural = _('Duty check-ins')
        unique_together = [['employee', 'duty_section']]
        ordering = ['-check_in_time']

    def __str__(self):
        return f"{self.employee} — {self.duty_section}"

    @property
    def is_active(self):
        return self.check_in_time is not None and self.check_out_time is None


class EmployeeLocationLog(models.Model):
    """Real-time joylashuv logi. BaseModel ishlatilmaydi — tezlik uchun."""
    employee = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='location_logs',
        help_text=_("Navbatchi")
    )
    duty_section = models.ForeignKey(
        'monitoring.DutySection', on_delete=models.CASCADE,
        related_name='location_logs',
        help_text=_("Bosqich")
    )
    latitude = models.DecimalField(
        _('Kenglik'), max_digits=9, decimal_places=6,
        help_text=_("GPS kenglik (lat)")
    )
    longitude = models.DecimalField(
        _('Uzunlik'), max_digits=9, decimal_places=6,
        help_text=_("GPS uzunlik (lon)")
    )
    accuracy = models.FloatField(
        _('Aniqlik'), null=True, blank=True,
        help_text=_("GPS aniqlik (metr)")
    )
    timestamp = models.DateTimeField(
        _('Vaqt'), auto_now_add=True, db_index=True
    )

    class Meta:
        verbose_name = _('Employee location log')
        verbose_name_plural = _('Employee location logs')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['employee', 'duty_section']),
            models.Index(fields=['duty_section', '-timestamp']),
        ]

    def __str__(self):
        return f"{self.employee} ({self.latitude}, {self.longitude}) @ {self.timestamp}"
