from django.contrib import admin
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.utils.translation import gettext_lazy as _

from users.models import User, Role, AppModule, UserJeton


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Shaxsiy ma\'lumotlar'), {'fields': (
            'last_name', 'first_name', 'second_name',
            'email', 'phone_number', 'avatar',
            'pinfl', 'date_of_birthday',
            'passport_series', 'passport_number',
        )}),
        (_('Tashkilot'), {'fields': (
            'organization', 'department', 'position',
            'special_rank', 'region', 'district', 'address',
        )}),
        (_('Ruxsatlar'), {'fields': (
            'is_active', 'is_staff', 'is_superuser',
            'roles', 'groups', 'user_permissions',
        )}),
        (_('Jeton'), {'fields': (
            'jeton_series', 'jeton_number', 'jeton_begin_date',
        )}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username', 'password1', 'password2',
                'last_name', 'first_name', 'second_name',
                'phone_number', 'organization', 'department', 'position',
                'region', 'district', 'roles', 'is_active', 'is_staff',
            ),
        }),
    )
    list_display = (
        'username', 'last_name', 'first_name',
        'phone_number', 'organization', 'district', 'is_active',
    )
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'roles', 'district')
    search_fields = ('username', 'last_name', 'first_name', 'second_name', 'pinfl', 'phone_number')
    ordering = ('username',)
    filter_horizontal = ('roles', 'groups', 'user_permissions')
    autocomplete_fields = ('organization', 'district', 'department', 'position', 'special_rank')
    list_select_related = ('organization', 'district')


@admin.register(Role)
class RoleAdmin(GroupAdmin):
    list_display = ('name', 'description', 'sorting')
    fields = ('name', 'description', 'permissions', 'sorting')
    search_fields = ('name', 'description')
    filter_horizontal = ('permissions',)


@admin.register(AppModule)
class AppModuleAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'on_dashboard')


@admin.register(UserJeton)
class UserJetonAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'jeton_series', 'jeton_number', 'begin_date')
    search_fields = ('name', 'jeton_series', 'jeton_number')
    list_filter = ('jeton_series',)
