from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.admin import UserAdmin, GroupAdmin

from users.models import User, Role, AppModule, UserJeton


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('last_name', 'first_name', 'second_name', 'email', 'avatar', 'avatar_base64', 'pinfl', 'date_of_birthday', 'passport_series', 'passport_number')}),
        (_('Permissions'),
         {'fields': ('is_active', 'is_staff', 'roles', 'client_token', 'address', 'region', 'district',
                    'jeton_series', 'jeton_number',
            'jeton_begin_date', 'special_rank', 'phone_number')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
            'last_name', 'first_name', 'second_name', 'email', 'gender', 'is_active', 'username', 'password1',
            'password2', 'roles', 'address', 'department', 'position', 'client_token', 'jeton_series', 'jeton_number',
            'jeton_begin_date', 'special_rank', 'phone_number'),
        }),
    )
    list_display = ('username', 'pinfl', 'last_name', 'first_name', 'second_name', 'phone_number', 'region', 'district', 'updated_time', 'updated_by')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'roles')
    search_fields = ('username', 'last_name', 'first_name', 'second_name', 'email', 'pinfl')
    ordering = ('username',)
    filter_horizontal = ('groups', 'user_permissions',)
    autocomplete_fields = ('district',)

    def is_admin(self, obj) -> bool:
        return obj.is_admin()

    is_admin.boolean = True


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
