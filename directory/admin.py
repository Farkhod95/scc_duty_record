from django.contrib import admin
from directory.models import (
    District, Region, Department, Position, Country, Organization,
    Mahalla, Nationality, SpecialRank, Location
)


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'region', 'district')
    fields = ('name', 'name_uz', 'name_uz_cyrl', 'name_ru', 'name_kaa', 'code', 'region', 'district')
    search_fields = ('name', 'name_uz', 'name_uz_cyrl', 'name_ru', 'name_kaa')
    autocomplete_fields = ('region', 'district')


@admin.register(SpecialRank)
class SpecialRankAdmin(admin.ModelAdmin):
    list_display = ('name',)
    fields = ('name', 'name_uz', 'name_uz_cyrl', 'name_ru', 'name_kaa')
    search_fields = ('name', 'name_uz', 'name_uz_cyrl', 'name_ru', 'name_kaa')


@admin.register(Nationality)
class NationalityAdmin(admin.ModelAdmin):
    list_display = ('name',)
    fields = ('name', 'name_uz', 'name_uz_cyrl', 'name_ru', 'name_kaa')
    search_fields = ('name', 'name_uz', 'name_uz_cyrl', 'name_ru', 'name_kaa')


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
    fields = ('name', 'name_uz', 'name_uz_cyrl', 'name_ru', 'name_kaa', 'code', 'migration_id')
    search_fields = ('name', 'name_uz', 'name_uz_cyrl', 'name_ru', 'name_kaa', 'code', 'migration_id')
    ordering = ('name',)
    list_per_page = 50


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
    fields = ('name', 'name_uz', 'name_uz_cyrl', 'name_ru', 'name_kaa', 'code',
              'path_topo_json')
    search_fields = ('name', 'code')


@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'region', 'is_active')
    fields = (
    'name', 'name_uz', 'name_uz_cyrl', 'name_ru', 'name_kaa', 'code', 'region', 'geo_json',
    'is_active')
    search_fields = ('name', 'code', 'region__name')
    list_filter = (
        'region',
    )


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name_uz', 'name_uz_cyrl', 'name_ru', 'name_kaa')
    fields = ('name', 'name_uz', 'name_uz_cyrl', 'name_ru', 'name_kaa')
    search_fields = ('name', 'name_uz', 'name_uz_cyrl', 'name_ru', 'name_kaa')


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ('name', 'department', 'name_uz', 'name_uz_cyrl', 'name_ru', 'name_kaa')
    fields = ('name', 'name_uz', 'name_uz_cyrl', 'name_ru', 'name_kaa', 'department')
    search_fields = ('name', 'name_uz', 'name_uz_cyrl', 'name_ru', 'name_kaa')


@admin.register(Mahalla)
class MahallaAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'name_uz', 'name_uz_cyrl', 'name_ru', 'name_kaa', 'region', 'district')
    fields = ('name', 'code', 'region', 'district', 'inn', 'new_inn')
    search_fields = ('name', 'code', 'name_uz', 'name_uz_cyrl', 'name_ru', 'name_kaa')
    list_filter = (
        'region',
        'district',
    )


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'key', 'region', 'district', 'created_time']
    list_filter = ['region', 'district', 'created_time']
    search_fields = ['title', 'key', 'region__name', 'district__name', 'district__code']
    readonly_fields = ['created_time', 'updated_time', 'created_by', 'updated_by']
