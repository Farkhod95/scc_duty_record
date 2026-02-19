from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from restapp.models import BaseModel


class TransportTypeChoices(models.TextChoices):
    CAR = 'CAR', _('Car')
    HORSE = 'HORSE', _('Horse')
    MOTORCYCLE = 'MOTORCYCLE', _('Motorcycle')
    FOOT = 'FOOT', _('Foot')


TRANSPORT_DEFAULT_CAPACITY = {
    TransportTypeChoices.CAR: 4,
    TransportTypeChoices.HORSE: 1,
    TransportTypeChoices.MOTORCYCLE: 1,
    TransportTypeChoices.FOOT: 1,
}


class TransportType(BaseModel):
    name = models.CharField(_('Name'), max_length=100, help_text=_("Transport turining nomi"))
    icon = models.TextField(_('Icon'), null=True, blank=True, help_text=_("SVG icon matni"))

    class Meta:
        verbose_name = _("Transport type")
        verbose_name_plural = _("Transport types")
        ordering = ['name']

    def __str__(self):
        return self.name


class Transport(BaseModel):
    organization = models.ForeignKey(
        'directory.Organization', on_delete=models.CASCADE,
        related_name='transports', help_text=_("Transport tegishli tashkilot")
    )
    type = models.ForeignKey(
        TransportType, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='transports', help_text=_("Transport turi (eski FK, vaqtinchalik)")
    )
    transport_type = models.CharField(
        _('Transport type'), max_length=20,
        choices=TransportTypeChoices.choices, default=TransportTypeChoices.CAR,
        help_text=_("Transport turi (CAR, HORSE, MOTORCYCLE, FOOT)")
    )
    name_or_code = models.CharField(
        _('Name or code'), max_length=100, null=True, blank=True,
        help_text=_("Transport nomi yoki kodi (masalan: 'Cobalt 01')")
    )
    plate_number = models.CharField(
        _('Plate number'), max_length=50, null=True, blank=True,
        help_text=_("Davlat raqami (faqat CAR uchun majburiy)")
    )
    capacity = models.PositiveIntegerField(
        _('Capacity'), default=4,
        help_text=_("Sig'imi (nechta odam sig'adi)")
    )
    number = models.CharField(_('Number'), max_length=50, help_text=_("Davlat raqami"))
    model = models.CharField(_('Model'), max_length=100, help_text=_("Transport modeli"))
    created_at = models.DateTimeField(auto_now_add=True, help_text=_("Yaratilgan sana"))

    class Meta:
        verbose_name = _("Transport")
        verbose_name_plural = _("Transports")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'transport_type']),
            models.Index(fields=['plate_number']),
        ]

    def __str__(self):
        if self.name_or_code:
            return f"{self.name_or_code} ({self.get_transport_type_display()})"
        return f"{self.model} - {self.number}"

    def clean(self):
        super().clean()
        if self.transport_type == TransportTypeChoices.CAR and not self.plate_number:
            raise ValidationError({
                'plate_number': _("Avtomobil uchun davlat raqami majburiy.")
            })
        max_capacity = TRANSPORT_DEFAULT_CAPACITY.get(self.transport_type, 4)
        if self.transport_type != TransportTypeChoices.CAR and self.capacity > max_capacity:
            raise ValidationError({
                'capacity': _(f"Bu transport turi uchun maksimal sig'im: {max_capacity}")
            })

    def save(self, *args, **kwargs):
        if not self.capacity or self._state.adding:
            self.capacity = TRANSPORT_DEFAULT_CAPACITY.get(self.transport_type, 4)
        super().save(*args, **kwargs)
