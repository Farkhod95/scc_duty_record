from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import Group, Permission
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from directory.serializers import RegionListSerializer, DistrictSerializer, PositionSerializer, \
    DepartmentListSerializer, CountrySerializer, OrganizationSerializer, SpecialRankListPublicSerializer
from .models import User, Role, AppModule, UserJeton


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ['id', 'codename']


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'name', 'sorting', 'description']


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['id', 'name']


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(style={'input_type': 'username'})
    password = serializers.CharField(style={'input_type': 'password'})


class UserSerializer(serializers.ModelSerializer):
    roles = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Role.objects.all(), required=False
    )
    organization_name = serializers.CharField(source='organization.name', read_only=True, default=None)
    region_name = serializers.CharField(source='region.name', read_only=True, default=None)
    district_name = serializers.CharField(source='district.name', read_only=True, default=None)
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'username', 'last_name', 'first_name', 'second_name', 'full_name', 'is_active',
            'date_of_birthday', 'gender', 'phone_number', 'avatar', 'email', 'special_rank',
            'date_joined', 'roles', 'password', 'organization', 'organization_name',
            'position', 'department',
            'region', 'region_name', 'district', 'district_name', 'address', 'pinfl', 'passport_series',
            'passport_number', 'passport_given_by', 'begin_date', 'end_date', 'avatar_base64',
            'jeton_series', 'jeton_number', 'jeton_begin_date', 'work_region',
            'work_district'
        )
        extra_kwargs = {
            'username': {
                'validators': [UnicodeUsernameValidator(), UniqueValidator(queryset=User.objects.all())],
            },
            'password': {'write_only': True, 'required': False},
        }

    def get_full_name(self, obj):
        parts = [obj.last_name, obj.first_name, obj.second_name]
        return ' '.join(p for p in parts if p)

    def create(self, validated_data):
        roles_ids = validated_data.pop('roles', [])
        password = validated_data.pop('password', None)

        user = User.objects.create(**validated_data)
        if password:
            user.password = make_password(password)
            # yoki: user.set_password(password)
        user.save()

        if roles_ids:
            user.roles.set(roles_ids)
        return user

    def update(self, instance, validated_data):
        roles_ids = validated_data.pop('roles', None)
        password = validated_data.pop('password', None)

        # oddiy maydonlarni yangilash
        for field, value in validated_data.items():
            setattr(instance, field, value)

        if password:
            instance.password = make_password(password)  # yoki instance.set_password(password)

        instance.save()

        if roles_ids is not None:
            instance.roles.set(roles_ids)

        return instance


class UserUpdateSchoolSerializer(serializers.ModelSerializer):
    roles = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Role.objects.all(),
        required=False
    )


    class Meta:
        model = User
        fields = (
            'id', 'username', 'last_name', 'first_name', 'second_name', 'is_active',
            'date_of_birthday', 'gender', 'phone_number', 'avatar', 'email', 'special_rank',
            'date_joined', 'roles', 'password', 'organization', 'position', 'department',
            'region', 'district', 'address', 'pinfl', 'passport_series',
            'passport_number', 'passport_given_by', 'begin_date', 'end_date', 'avatar_base64',
            'jeton_series', 'jeton_number', 'jeton_begin_date',
            'work_region', 'work_district',
        )
        extra_kwargs = {
            'username': {
                'validators': [UnicodeUsernameValidator(), UniqueValidator(queryset=User.objects.all())],
                'required': False,
            },
            'password': {'write_only': True, 'required': False},
        }

    def update(self, instance, validated_data):

        validated_data.pop('roles', None)     # roles bu endpoint orqali o'zgarmaydi
        validated_data.pop('password', None)  # password ham

        # Faqat shu oddiy fieldlarni o'zgartirishga ruxsat beramiz
        ALLOWED_SIMPLE_FIELDS = ['work_region', 'work_district']


        # 2) Oddiy fieldlarni yangilash (FAQAT work_region, work_district)
        for field, value in validated_data.items():
            if field in ALLOWED_SIMPLE_FIELDS:
                setattr(instance, field, value)

        instance.save()
        return instance



class UsernameCheckSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=255, trim_whitespace=True)


class UserListPublicSerializer(serializers.ModelSerializer):
    role_detail = RoleSerializer(source='roles', many=True, read_only=True)
    work_region_detail = RegionListSerializer(source='work_region', read_only=True)
    work_district_detail = DistrictSerializer(source='work_district', read_only=True)

    class Meta:
        model = User
        fields = (
            'id', 'username', 'last_name', 'first_name', 'second_name', 'date_of_birthday', 'pinfl', 'roles',
            'role_detail', 'phone_number', 'passport_series', 'passport_number', 'work_region', 'work_district',
            'work_region_detail', 'work_district_detail', 'avatar_base64')



class UserListNotifSerializer(serializers.ModelSerializer):
    role_detail = RoleSerializer(source='roles', many=True, read_only=True)

    class Meta:
        model = User
        fields = (
            'id', 'username', 'last_name', 'first_name', 'second_name', 'date_of_birthday', 'pinfl', 'roles',
            'role_detail', 'phone_number', 'passport_series', 'passport_number', 'work_region', 'work_district')


class UserListPublicInspektorSerializer(serializers.ModelSerializer):
    special_rank_detail = SpecialRankListPublicSerializer(source='special_rank', read_only=True)
    work_region_detail = RegionListSerializer(source='work_region', read_only=True)
    work_district_detail = DistrictSerializer(source='work_district', read_only=True)

    class Meta:
        model = User
        fields = (
            'id', 'username', 'last_name', 'first_name', 'second_name', 'date_of_birthday', 'gender',
            'phone_number', 'special_rank', 'special_rank_detail', 'pinfl', 'passport_series', 'passport_number',
            'work_region', 'work_district', 'work_region_detail', 'work_district_detail')


class UserListPublicIdSerializer(serializers.ModelSerializer):
    role_detail = RoleSerializer(source='roles', many=True, read_only=True)
    special_rank_detail = SpecialRankListPublicSerializer(source='special_rank', read_only=True)
    region_detail = RegionListSerializer(source='region', read_only=True)
    district_detail = DistrictSerializer(source='district', read_only=True)
    work_region_detail = RegionListSerializer(source='work_region', read_only=True)
    work_district_detail = DistrictSerializer(source='work_district', read_only=True)
    organization_detail = OrganizationSerializer(source='organization', read_only=True)
    position_detail = PositionSerializer(source='position', read_only=True)
    department_detail = DepartmentListSerializer(source='department', read_only=True)

    sortings = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'username', 'last_name', 'first_name', 'second_name', 'is_active', 'date_of_birthday', 'gender',
            'phone_number', 'avatar', 'email', 'special_rank', 'special_rank_detail', 'sortings',
            'date_joined', 'roles', 'role_detail', 'password', 'organization', 'organization_detail', 'position',
            'position_detail', 'department_detail', 'department', 'region',
            'region_detail', 'district', 'district_detail', 'address', 'pinfl', 'passport_series', 'passport_number',
            'passport_given_by', 'begin_date', 'end_date', 'avatar_base64', 'jeton_series', 'jeton_number',
            'jeton_begin_date',
            'work_region', 'work_district', 'work_region_detail', 'work_district_detail', )

    def get_avatar(self, obj):
        """
        Natija:
        - avatar bo'lsa => https://domain.com/assets/avatars/...
        - bo'lmasa => None
        """
        if not obj.avatar:
            return None

        request = self.context.get("request")
        # avatar.url odatda "/assets/..." yoki "/media/..." bo'ladi
        url = obj.avatar.url

        # request bo'lsa to'liq qilib beradi
        if request:
            return request.build_absolute_uri(url)

        # request kelmasa fallback (kamdan-kam holat)
        return url

    def get_sortings(self, obj):
        """
        User.roles dan faqat sorting qiymatlarini massiv qilib qaytaradi.
        Masalan: [1, 3, 5]
        """
        # null bo‘lgan sortinglarni chiqarib tashlaymiz va tartib bo‘yicha sort qilamiz
        qs = obj.roles.exclude(sorting__isnull=True).order_by('sorting')
        return list(qs.values_list('sorting', flat=True))



class UserMobilListPublicIdSerializer(serializers.ModelSerializer):
    role_detail = RoleSerializer(source='roles', many=True, read_only=True)
    special_rank_detail = SpecialRankListPublicSerializer(source='special_rank', read_only=True)
    region_detail = RegionListSerializer(source='region', read_only=True)
    district_detail = DistrictSerializer(source='district', read_only=True)
    work_region_detail = RegionListSerializer(source='work_region', read_only=True)
    work_district_detail = DistrictSerializer(source='work_district', read_only=True)
    organization_detail = OrganizationSerializer(source='organization', read_only=True)
    position_detail = PositionSerializer(source='position', read_only=True)
    department_detail = DepartmentListSerializer(source='department', read_only=True)

    class Meta:
        model = User
        fields = (
            'id', 'username', 'last_name', 'first_name', 'second_name', 'is_active', 'date_of_birthday', 'gender',
            'phone_number', 'avatar', 'email', 'special_rank', 'special_rank_detail',
            'date_joined', 'roles', 'role_detail', 'password', 'organization', 'organization_detail', 'position',
            'position_detail', 'department_detail', 'department', 'region',
            'region_detail', 'district', 'district_detail', 'address', 'pinfl', 'passport_series', 'passport_number',
            'passport_given_by', 'begin_date', 'end_date', 'jeton_series', 'jeton_number',
            'jeton_begin_date',
            'work_region', 'work_district', 'work_region_detail', 'work_district_detail')



class UserListSerializer(serializers.ModelSerializer):
    role_detail = RoleSerializer(source='roles', many=True, read_only=True)
    organization_detail = OrganizationSerializer(source='organization', read_only=True)
    region_name = serializers.CharField(source='region.name', read_only=True, default=None)
    district_name = serializers.CharField(source='district.name', read_only=True, default=None)

    class Meta:
        model = User
        fields = (
            'id', 'username', 'last_name', 'first_name', 'second_name', 'is_active', 'date_of_birthday', 'gender',
            'phone_number', 'avatar', 'email', 'special_rank', 'organization', 'organization_detail',
            'date_joined', 'roles', 'role_detail', 'password', 'organization', 'position', 'department', 'region',
            'region_name', 'district', 'district_name', 'address', 'pinfl', 'passport_series',
            'passport_number', 'passport_given_by', 'begin_date',
            'end_date', 'avatar_base64', 'jeton_series', 'jeton_number', 'jeton_begin_date')


class RelatedUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, allow_blank=True, required=False)

    class Meta:
        model = User
        fields = ('id', 'username', 'password')
        extra_kwargs = {
            'username': {
                'validators': [UnicodeUsernameValidator(), UniqueValidator(queryset=User.objects.all())],
            }
        }


class RelatedUserPutSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, allow_blank=True, required=False)

    class Meta:
        model = User
        fields = ('id', 'username', 'password')
        extra_kwargs = {
            'username': {
                'validators': [],
            }
        }


class ContentTypeSerializer(serializers.ModelSerializer):
    permissions = serializers.SerializerMethodField(method_name='get_permissions')

    class Meta:
        model = ContentType
        fields = ('id', 'model', 'permissions')

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        if hasattr(instance, 'extendedcontenttype'):
            ret['model'] = instance.extendedcontenttype.extend_name.upper()
        else:
            ret['model'] = ret['model'].upper()
        return ret

    def get_permissions(self, instance):
        permissions = Permission.objects.filter(content_type=instance.id)
        result = []
        for p in permissions:
            result.append(
                {"id": p.id, "name": p.codename.split('_')[0].upper()}
            )
        return result


class AppModuleSerializer(serializers.ModelSerializer):
    modules = ContentTypeSerializer(source='content_types', read_only=True, many=True)

    class Meta:
        model = AppModule
        fields = ('id', 'name', 'modules', 'sorting')


class ChangePasswordSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    password2 = serializers.CharField(write_only=True, required=True)
    old_password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('old_password', 'password', 'password2')

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})

        return attrs

    def validate_old_password(self, value):
        user = self.instance
        if not user.check_password(value):
            raise serializers.ValidationError({"old_password": "Old password is not correct"})
        return value

    def update(self, instance, validated_data):

        instance.set_password(validated_data['password'])
        instance.save()
        return instance



class UserJetonSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserJeton
        fields = ('id', 'user', 'name', 'jeton_series', 'jeton_number', 'begin_date')
