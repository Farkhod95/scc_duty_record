from rest_framework import serializers

from .models import Region, District, Position, Department, Country, Mahalla,  Organization, Nationality, SpecialRank


# Tarjima asosiy serializeri
class LocaleSerializer(serializers.ModelSerializer):
    name_uz = serializers.CharField(allow_blank=False)
    name_uz_cyrl = serializers.CharField(allow_blank=False)
    name_ru = serializers.CharField(allow_blank=False)
    name_kaa = serializers.CharField(allow_blank=False)


class SpecialRankSerializer(LocaleSerializer):
    class Meta:
        model = SpecialRank
        fields = ('id', 'name', 'name_uz', 'name_uz_cyrl', 'name_ru', 'name_kaa')
        extra_kwargs = {
            'name_uz': {"required": True},
            'name_uz_cyrl': {"required": True},
            'name_ru': {"required": True},
            'name_kaa': {"required": True},
        }


class SpecialRankListSerializer(LocaleSerializer):
    class Meta:
        model = SpecialRank
        fields = ('id', 'name', 'name_uz', 'name_uz_cyrl', 'name_ru', 'name_kaa')


class SpecialRankListPublicSerializer(LocaleSerializer):
    class Meta:
        model = SpecialRank
        fields = ('id', 'name',)


class NationalitySerializer(LocaleSerializer):
    class Meta:
        model = Nationality
        fields = ('id', 'name', 'name_uz', 'name_uz_cyrl', 'name_ru', 'name_kaa')
        extra_kwargs = {
            'code': {"required": True},
            'name_uz': {"required": True},
            'name_uz_cyrl': {"required": True},
            'name_ru': {"required": True},
            'name_kaa': {"required": True},
        }


class NationalityListSerializer(LocaleSerializer):
    class Meta:
        model = Nationality
        fields = ('id', 'name', 'name_uz', 'name_uz_cyrl', 'name_ru', 'name_kaa')


class NationalityListPublicSerializer(LocaleSerializer):
    class Meta:
        model = Nationality
        fields = ('id', 'name',)


class CountrySerializer(LocaleSerializer):
    class Meta:
        model = Country
        fields = ('id', 'code', 'name', 'name_uz', 'name_uz_cyrl', 'name_ru', 'name_kaa', 'migration_id')
        extra_kwargs = {
            'code': {"required": True},
            'name_uz': {"required": True},
            'name_uz_cyrl': {"required": True},
            'name_ru': {"required": True},
            'name_kaa': {"required": True},
        }


class CountryListSerializer(LocaleSerializer):
    class Meta:
        model = Country
        fields = ('id', 'code', 'name', 'migration_id')


class RelatedRegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = ('id', 'name')


class RelatedDistrictSerializer(serializers.ModelSerializer):
    class Meta:
        model = District
        fields = ('id', 'name')


class RelatedPositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = ('id', 'name')


class RegionSerializer(LocaleSerializer):
    class Meta:
        model = Region
        fields = (
        'id', 'code', 'name', 'name_uz', 'name_uz_cyrl', 'name_ru', 'name_kaa')
        extra_kwargs = {
            'code': {"required": True},
            'name_uz': {"required": True},
            'name_uz_cyrl': {"required": True},
            'name_ru': {"required": True},
            'name_kaa': {"required": True},
        }


class RegionListSerializer(LocaleSerializer):
    class Meta:
        model = Region
        fields = (
        'id', 'code', 'name', 'name_uz', 'name_uz_cyrl', 'name_ru', 'name_kaa')


class RegionListPublicSerializer(LocaleSerializer):
    class Meta:
        model = Region
        fields = ('id', 'code', 'name')


class RegionListPublicSerializer(LocaleSerializer):
    class Meta:
        model = District
        fields = ('id', 'code', 'name', 'is_active')


class DistrictListPublicSerializer(LocaleSerializer):
    class Meta:
        model = District
        fields = ('id', 'code', 'name', 'is_active')


class DistrictListSerializer(LocaleSerializer):
    region_detail = RegionListSerializer(source='region', read_only=True)

    class Meta:
        model = District
        fields = (
            'id', 'code', 'name', 'name_uz', 'name_uz_cyrl', 'name_ru', 'name_kaa', 'region', 'region_detail', 'is_active')


class DistrictSerializer(LocaleSerializer):
    class Meta:
        model = District
        fields = (
            'id', 'code', 'name', 'name_uz', 'name_uz_cyrl', 'name_ru', 'name_kaa', 'region',  'is_active')
        extra_kwargs = {
            'code': {"required": True},
            'region': {"required": True},
            'name_uz': {"required": True},
            'name_uz_cyrl': {"required": True},
            'name_ru': {"required": True},
            'name_kaa': {"required": True},
        }


class MahallaSerializer(LocaleSerializer):
    class Meta:
        model = Mahalla
        fields = (
            'id', 'code', 'name', 'name_uz', 'name_uz_cyrl', 'name_ru', 'name_kaa', 'region', 'district', 'inn', 'new_inn', )
        extra_kwargs = {
            'code': {"required": True},
            'region': {"required": True},
            'district': {"required": True},
            'name_uz': {"required": True},
            'name_uz_cyrl': {"required": True},
            'name_ru': {"required": True},
            'name_kaa': {"required": True},
        }


class MahallaListSerializer(LocaleSerializer):
    region_detail = RegionListSerializer(source='region', read_only=True)
    district_detail = DistrictListPublicSerializer(source='district', read_only=True)

    class Meta:
        model = Mahalla
        fields = (
            'id', 'code', 'name', 'name_uz', 'name_uz_cyrl', 'name_ru', 'name_kaa', 'region', 'district',
            'region_detail', 'district_detail', 'inn', 'new_inn')


class MahallaListPublicSerializer(LocaleSerializer):
    class Meta:
        model = Mahalla
        fields = ('id', 'code', 'name')


class OrganizationSerializer(LocaleSerializer):
    class Meta:
        model = Organization
        fields = ('id', 'name', 'number', 'code', 'name_uz', 'name_uz_cyrl', 'name_ru', 'name_kaa', 'region',
                  'district')
        extra_kwargs = {
            'code': {"required": True},
            'name_uz': {"required": True},
            'name_uz_cyrl': {"required": True},
            'name_ru': {"required": True},
            'name_kaa': {"required": True},
        }


class OrganizationListSerializer(LocaleSerializer):
    class Meta:
        model = Organization
        fields = ('id', 'name', 'number', 'code', 'name_uz', 'name_uz_cyrl', 'name_ru', 'name_kaa', 'region',
                  'district')


class OrganizationListPublicSerializer(LocaleSerializer):
    class Meta:
        model = Organization
        fields = ('id', 'name', 'number', 'code')


class DepartmentSerializer(LocaleSerializer):
    class Meta:
        model = Department
        fields = ('id', 'name', 'name_uz', 'name_uz_cyrl', 'name_ru', 'name_kaa', 'organization')
        extra_kwargs = {
            'organization': {"required": True},
            'name_uz': {"required": True},
            'name_uz_cyrl': {"required": True},
            'name_ru': {"required": True},
            'name_kaa': {"required": True},
        }


class DepartmentListSerializer(LocaleSerializer):
    organization_detail = OrganizationListPublicSerializer(source="organization", read_only=True)

    class Meta:
        model = Department
        fields = ('id', 'name', 'name_uz', 'name_uz_cyrl', 'name_ru', 'name_kaa', 'organization', 'organization_detail')


class DepartmentListPublicSerializer(LocaleSerializer):
    class Meta:
        model = Department
        fields = ('id', 'name')


class PositionSerializer(LocaleSerializer):
    class Meta:
        model = Position
        fields = ('id', 'name', 'name_uz', 'name_uz_cyrl', 'name_ru', 'name_kaa', 'department')
        extra_kwargs = {
            'department': {"required": True},
            'name_uz': {"required": True},
            'name_uz_cyrl': {"required": True},
            'name_ru': {"required": True},
            'name_kaa': {"required": True},
        }


class PositionListSerializer(LocaleSerializer):
    department_detail = DepartmentListPublicSerializer(source="department", read_only=True)

    class Meta:
        model = Position
        fields = ('id', 'name', 'name_uz', 'name_uz_cyrl', 'name_ru', 'name_kaa', 'department', 'department_detail')


class PositionListPublicSerializer(LocaleSerializer):
    class Meta:
        model = Position
        fields = ('id', 'name')
