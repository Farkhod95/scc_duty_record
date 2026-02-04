from django_filters.rest_framework import FilterSet
from django_filters import rest_framework as filters
from django_filters import rest_framework as df
from directory.models import District, Region, Position, Department, Country, Mahalla, Organization, Nationality, \
    SpecialRank, Location


class NumberInFilter(df.BaseInFilter, df.NumberFilter):
    pass

class SpecialRankFilter(FilterSet):

    class Meta:
        model = SpecialRank
        fields = {
            'name': ['exact'],
        }


class NationalityFilter(FilterSet):

    class Meta:
        model = Nationality
        fields = {
            'name': ['exact'],
        }



class DistrictFilter(df.FilterSet):
    code   = df.CharFilter(field_name='code', lookup_expr='istartswith')
    name   = df.CharFilter(field_name='name', lookup_expr='istartswith')
    region = NumberInFilter(field_name='region_id', lookup_expr='in')
    is_active = df.BooleanFilter(field_name='is_active')

    class Meta:
        model = District
        fields = [
            'code', 'name', 'region', 'is_active'
        ]


class CountrysFilter(FilterSet):

    class Meta:
        model = Country
        fields = {
            'name': ['exact'],
            'code': ['exact'],
        }


class RegionssFilter(FilterSet):

    class Meta:
        model = Region
        fields = {
            'name': ['exact'],
            'code': ['exact'],
        }


class OrganizationFilter(FilterSet):

    class Meta:
        model = Organization
        fields = {
            'number': ['exact'],
            'code': ['exact'],
        }


class PositionFilter(FilterSet):

    class Meta:
        model = Position
        fields = {
            'name': ['exact'],
            'department': ['exact'],
        }


class DepartmentFilter(FilterSet):

    class Meta:
        model = Department
        fields = {
            'name': ['exact'],
        }


class MahallaFilter(FilterSet):
    class Meta:
        model = Mahalla
        fields = {
            'name': ['exact', 'icontains'],
            'code': ['exact'],
            'region': ['exact'],
            'district': ['exact'],
        }


class LocationFilter(FilterSet):
    class Meta:
        model = Location
        fields = {
            'region': ['exact'],
            'district': ['exact'],
            'title': ['exact', 'icontains'],
            'key': ['exact'],
        }