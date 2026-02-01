from django.db import models
from django.utils.translation import gettext_lazy as _

from restapp.models import BaseModel


class TransportType(BaseModel):
    name = models.CharField(_('Name'), max_length=100, help_text=_("Transport turining nomi"))
    icon_url = models.URLField(_('Icon URL'), max_length=500, help_text=_("Mapda chizish uchun ikonka URL manzili"))

    class Meta:
        verbose_name = _("Transport type")
        verbose_name_plural = _("Transport types")
        ordering = ['name']

    def __str__(self):
        return self.name


class Transport(BaseModel):
    organization = models.ForeignKey('directory.Organization', on_delete=models.CASCADE, related_name='transports', help_text=_("Transport tegishli tashkilot"))
    type = models.ForeignKey(TransportType, on_delete=models.PROTECT, related_name='transports', help_text=_("Transport turi (avtomobil, yuk mashinasi va h.k.)"))
    number = models.CharField(_('Number'), max_length=50, help_text=_("Davlat raqami"))
    model = models.CharField(_('Model'), max_length=100, help_text=_("Transport modeli"))
    created_at = models.DateTimeField(auto_now_add=True,help_text=_("Yaratilgan sana"))

    class Meta:
        verbose_name = _("Transport")
        verbose_name_plural = _("Transports")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'type']),
            models.Index(fields=['number']),
        ]

    def __str__(self):
        return f"{self.model} - {self.number}"