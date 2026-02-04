from django.db import models
from django.utils.translation import gettext_lazy as _

from restapp.models import BaseModel


class SpecialRank(BaseModel):
    name = models.CharField(max_length=255, null=True, blank=True, help_text=_("Millat nomi"))

    class Meta:
        verbose_name = _('Special rank')
        verbose_name_plural = _('Special ranks')

    def __str__(self):
        return self.name


class Nationality(BaseModel):
    name = models.CharField(max_length=255, null=True, blank=True, help_text=_("Millat nomi"))

    class Meta:
        verbose_name = _('Nationality')
        verbose_name_plural = _('Nationality')

    def __str__(self):
        return self.name


class Country(BaseModel):
    code = models.CharField(_('Country code'), max_length=50, null=True, blank=True, help_text=_("Mamlakat kodi"))
    name = models.CharField(max_length=255, null=True, blank=True, help_text=_("Mamlakat nomi"))
    migration_id = models.IntegerField(null=True, blank=True, help_text=_("Migration Mamlakat Id"))


    class Meta:
        verbose_name = _('Country')
        verbose_name_plural = _('Countries')

    def __str__(self):
        return self.name


class Region(BaseModel):
    code = models.CharField(_('Region code'), max_length=50, null=True, blank=True, help_text=_("Viloyat kodi"))
    name = models.CharField(max_length=255, null=True, blank=True, help_text=_("Viloyat nomi"))
    geo_json = models.TextField(_('GeoJson'), blank=True, help_text=_("Deo json"))

    class Meta:
        verbose_name = _('region')
        verbose_name_plural = _('regions')

    def __str__(self):
        return f"{self.name} ({self.code})"


class District(BaseModel):
    code = models.CharField(_('District code'), max_length=50, null=True, blank=True, db_index=True, help_text=_("Tuman kodi"))
    name = models.CharField(_('District name'), max_length=255, null=True, blank=True, help_text=_("Tuman nomi"))
    region = models.ForeignKey(Region, related_name='districts', on_delete=models.SET_NULL, null=True, blank=True, help_text=_("Viloyat jadvali bilan bog'lanish"))
    geo_json = models.TextField(_('GeoJson'), blank=True, help_text=_("Geo json"))
    is_active = models.BooleanField(_('Active'), default=True, help_text=_("District holati"))

    class Meta:
        verbose_name = _('district')
        verbose_name_plural = _('districts')

    def __str__(self):
        return f"{self.name} ({self.code})"


class Mahalla(BaseModel):
    code = models.CharField(_('Mahalla code'), max_length=50, null=True, blank=True, help_text=_("Mahalla kodi"))
    name = models.CharField(_('Mahalla name'), max_length=255, null=True, blank=True, help_text=_("Mahalla nomi"))
    region = models.ForeignKey(Region, related_name='mahalla_region', on_delete=models.SET_NULL, null=True, blank=True, help_text=_("Viloyat jadvali bilan bog'lanish"))
    district = models.ForeignKey(District, related_name='mahalla_district', on_delete=models.SET_NULL, null=True,
                                 blank=True, help_text=_("Tuman jadvali bilan bog'lanish"))
    inn = models.CharField(_('INN name'), max_length=255, null=True, blank=True, help_text=_("Mahalla INN"))
    new_inn = models.CharField(_('INN name'), max_length=255, null=True, blank=True, help_text=_("Mahalla INN"))

    class Meta:
        verbose_name = _('Mahalla')
        verbose_name_plural = _('Mahalla')

    def __str__(self):
        return self.name



class Organization(BaseModel):
    name = models.CharField(_('Organization name'), max_length=255, null=True, blank=True,
                            help_text=_("Tashkilotning to‘liq nomini kiriting"))
    number = models.CharField(_('Number'), max_length=255, null=True, blank=True,
                              help_text=_("Tashkilotning raqamini yoki tartib raqamini kiriting"))
    code = models.CharField(_('Code'), max_length=255, null=True, blank=True,
                            help_text=_("Tashkilotning kodini kiriting (agar mavjud bo‘lsa)"))
    region = models.ForeignKey(Region, related_name='organ_region', on_delete=models.SET_NULL, null=True, blank=True,
                               help_text=_("Viloyat jadvali bilan bog'lanish"))
    district = models.ForeignKey(District, related_name='organ_district', on_delete=models.SET_NULL, null=True,
                                 blank=True, help_text=_("Tuman jadvali bilan bog'lanish"))

    class Meta:
        verbose_name = _('Organization')
        verbose_name_plural = _('Organizations')
        indexes = [
            models.Index(fields=['region', 'district']),
        ]

    def __str__(self):
        return self.name


class Department(BaseModel):
    name = models.CharField(_('Department name'), max_length=255, null=True, blank=True,
                            help_text=_("Bo‘limning nomini kiriting"))
    organization = models.ForeignKey(Organization, related_name='departments', on_delete=models.SET_NULL, null=True,
                                     blank=True, help_text=_("Bo‘lim tegishli tashkilotni tanlang"))

    class Meta:
        verbose_name = _('department')
        verbose_name_plural = _('departments')

    def __str__(self):
        return self.name


class Position(BaseModel):
    name = models.CharField(_('Position name'), max_length=255, null=True, blank=True,
                            help_text=_("Lavozim nomini kiriting"))
    department = models.ForeignKey(Department, related_name='positions', on_delete=models.SET_NULL, null=True,
                                   blank=True, help_text=_("Lavozim tegishli bo‘lgan bo‘limni tanlang"))

    class Meta:
        verbose_name = _('position')
        verbose_name_plural = _('positions')

    def __str__(self):
        return self.name


class Location(BaseModel):
    region = models.ForeignKey(Region, related_name='locations', on_delete=models.SET_NULL, null=True, blank=True)
    district = models.ForeignKey(District, related_name='locations', on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(_('Title'), max_length=255, help_text=_("Location nomi"))
    key = models.CharField(_('Key'), max_length=100, unique=True, help_text=_("Location unique key/kodi"))
    boundary_data = models.JSONField(null=True, blank=True)

    class Meta:
        verbose_name = _('location')
        verbose_name_plural = _('locations')
        ordering = ['title']
        indexes = [
            models.Index(fields=['key']),
            models.Index(fields=['region']),
            models.Index(fields=['district']),
        ]

    def __str__(self):
        return f"{self.title} ({self.key})"