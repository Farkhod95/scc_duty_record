from rest_framework import serializers

from .models import Region, District, Position, Department, Country, Mahalla, Organization, Nationality, SpecialRank, Location, LocationPoint


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


class RegionDetailSerializer(LocaleSerializer):
    class Meta:
        model = Region
        fields = (
        'id', 'code', 'name', 'name_uz', 'name_uz_cyrl', 'name_ru', 'name_kaa', 'boundary_data')


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


class DistrictDetailSerializer(LocaleSerializer):
    region_detail = RegionListSerializer(source='region', read_only=True)

    class Meta:
        model = District
        fields = (
            'id', 'code', 'name', 'name_uz', 'name_uz_cyrl', 'name_ru', 'name_kaa', 'region', 'region_detail', 'is_active', 'boundary_data')


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


class MahallaDetailSerializer(LocaleSerializer):
    region_detail = RegionListSerializer(source='region', read_only=True)
    district_detail = DistrictListPublicSerializer(source='district', read_only=True)

    class Meta:
        model = Mahalla
        fields = (
            'id', 'code', 'name', 'name_uz', 'name_uz_cyrl', 'name_ru', 'name_kaa', 'region', 'district',
            'region_detail', 'district_detail', 'inn', 'new_inn', 'boundary_data')


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
    region_name = serializers.CharField(source='region.name', read_only=True, default=None)
    district_name = serializers.CharField(source='district.name', read_only=True, default=None)

    class Meta:
        model = Organization
        fields = ('id', 'name', 'number', 'code', 'name_uz', 'name_uz_cyrl', 'name_ru', 'name_kaa', 'region',
                  'region_name', 'district', 'district_name')


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


class LocationPointSerializer(serializers.ModelSerializer):
    class Meta:
        model = LocationPoint
        fields = ['id', 'order', 'name', 'latitude', 'longitude', 'start_time', 'end_time']


class LocationSerializer(serializers.ModelSerializer):
    mahallas = serializers.PrimaryKeyRelatedField(
        queryset=Mahalla.objects.all(), many=True, required=False
    )

    class Meta:
        model = Location
        fields = [
            'id', 'region', 'district', 'title', 'boundary_data', 'mahallas',
            'created_time', 'updated_time', 'created_by', 'updated_by'
        ]
        read_only_fields = ['id', 'created_time', 'updated_time', 'created_by', 'updated_by']

    def validate_boundary_data(self, value):
        if value and not isinstance(value, dict):
            raise serializers.ValidationError("Boundary data dict bo'lishi kerak")
        return value


class LocationListSerializer(serializers.ModelSerializer):
    region_name = serializers.CharField(source='region.name', read_only=True, allow_null=True)
    district_name = serializers.CharField(source='district.name', read_only=True, allow_null=True)
    has_boundary = serializers.SerializerMethodField()
    mahallas_count = serializers.SerializerMethodField()

    class Meta:
        model = Location
        fields = [
            'id', 'region', 'region_name', 'district', 'district_name',
            'title', 'has_boundary', 'mahallas_count', 'created_time'
        ]

    def get_has_boundary(self, obj):
        return obj.boundary_data is not None and bool(obj.boundary_data)

    def get_mahallas_count(self, obj):
        return obj.mahallas.count()


class LocationDetailSerializer(serializers.ModelSerializer):
    region_name = serializers.CharField(source='region.name', read_only=True, allow_null=True)
    region_code = serializers.CharField(source='region.code', read_only=True, allow_null=True)
    district_name = serializers.CharField(source='district.name', read_only=True, allow_null=True)
    district_code = serializers.CharField(source='district.code', read_only=True, allow_null=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    updated_by_name = serializers.CharField(source='updated_by.get_full_name', read_only=True)
    mahallas = serializers.SerializerMethodField()
    points = LocationPointSerializer(many=True, read_only=True)

    def get_mahallas(self, obj):
        return [{'id': m.pk, 'name': m.name} for m in obj.mahallas.all()]

    class Meta:
        model = Location
        fields = [
            'id', 'region', 'region_name', 'region_code',
            'district', 'district_name', 'district_code',
            'title', 'boundary_data', 'mahallas', 'points',
            'created_time', 'updated_time',
            'created_by', 'created_by_name',
            'updated_by', 'updated_by_name'
        ]