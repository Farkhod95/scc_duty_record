from django.db import models
from django.utils.translation import gettext_lazy as _

from restapp.models import BaseModel



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
        related_name='transports', help_text=_("Transport turi")
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
            models.Index(fields=['organization', 'type']),
            models.Index(fields=['plate_number']),
        ]

    def __str__(self):
        if self.name_or_code:
            type_name = self.type.name if self.type else ''
            return f"{self.name_or_code} ({type_name})" if type_name else self.name_or_code
        return f"{self.model} - {self.number}"
