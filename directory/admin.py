from django.contrib import admin

from directory.models import (
    Country, Nationality, Region, District, Mahalla,
    Department, Position, SpecialRank, Location, LocationPoint,
    Organization, OrgStageDefinition,
)


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'migration_id')
    search_fields = ('name', 'code')
    ordering = ('name',)


@admin.register(Nationality)
class NationalityAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
    search_fields = ('name', 'code')
    readonly_fields = ('boundary_data',)


@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'region', 'is_active')
    search_fields = ('name', 'code')
    list_filter = ('region', 'is_active')
    autocomplete_fields = ('region',)
    readonly_fields = ('boundary_data',)


@admin.register(Mahalla)
class MahallaAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'district', 'region')
    search_fields = ('name', 'code')
    list_filter = ('region', 'district')
    autocomplete_fields = ('region', 'district')
    readonly_fields = ('boundary_data',)
    list_select_related = ('region', 'district')


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ('name', 'department')
    search_fields = ('name',)
    list_filter = ('department',)
    autocomplete_fields = ('department',)


@admin.register(SpecialRank)
class SpecialRankAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


class LocationPointInline(admin.TabularInline):
    model = LocationPoint
    extra = 0
    fields = ('order', 'name', 'latitude', 'longitude', 'start_time', 'end_time')
    ordering = ('order',)


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('title', 'region', 'district', 'created_time')
    search_fields = ('title',)
    list_filter = ('region', 'district')
    filter_horizontal = ('mahallas',)
    readonly_fields = ('created_time', 'updated_time', 'created_by', 'updated_by')
    inlines = [LocationPointInline]


class OrgStageDefinitionInline(admin.TabularInline):
    model = OrgStageDefinition
    extra = 0
    fields = ('stage_number', 'name', 'default_start_time', 'default_end_time')
    ordering = ('stage_number',)


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'region', 'district', 'stages_count')
    search_fields = ('name', 'code')
    list_filter = ('region', 'district')
    autocomplete_fields = ('region', 'district')
    inlines = [OrgStageDefinitionInline]
    list_select_related = ('region', 'district')
