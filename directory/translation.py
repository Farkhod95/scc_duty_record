from modeltranslation.translator import register, TranslationOptions

from .models import Region, District, Department, Position, Mahalla, Country, Organization, Nationality, SpecialRank


@register(SpecialRank)
class SpecialRankTranslationOptions(TranslationOptions):
    fields = ('name',)


@register(Nationality)
class NationalityTranslationOptions(TranslationOptions):
    fields = ('name',)


@register(Country)
class CountryTranslationOptions(TranslationOptions):
    fields = ('name',)


@register(Region)
class RegionTranslationOptions(TranslationOptions):
    fields = ('name',)


@register(District)
class DistrictTranslationOptions(TranslationOptions):
    fields = ('name',)


@register(Mahalla)
class MahallaTranslationOptions(TranslationOptions):
    fields = ('name',)


@register(Organization)
class OrganizationTranslationOptions(TranslationOptions):
    fields = ('name',)


@register(Department)
class DepartmentTranslationOptions(TranslationOptions):
    fields = ('name',)


@register(Position)
class PositionTranslationOptions(TranslationOptions):
    fields = ('name',)
