from itertools import groupby
from operator import itemgetter

from rest_framework.permissions import BasePermission


class IsSuperAdmin(BasePermission):
    """Faqat superadmin uchun ruxsat"""
    message = "Faqat superadmin bu amalni bajarishi mumkin"

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.is_superuser or request.user.is_superadmin()


class IsOrgAdmin(BasePermission):
    """Organizatsiya admini uchun ruxsat (superadmin ham o'tadi)"""
    message = "Sizda bu amalni bajarish huquqi yo'q"

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser or request.user.is_superadmin():
            return True
        if request.user.is_admin() or request.user.is_manager():
            return request.user.organization_id is not None
        return False


class IsManager(BasePermission):
    """Manager roli uchun ruxsat (superadmin ham o'tadi)"""
    message = "Faqat Manager bu amalni bajarishi mumkin"

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser or request.user.is_superadmin():
            return True
        return request.user.is_manager()


class IsOrgMember(BasePermission):
    """Faqat o'z organizatsiyasidagi ma'lumotlarni ko'rish/tahrirlash"""
    message = "Siz faqat o'z organizatsiyangiz ma'lumotlarini ko'ra olasiz"

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser or request.user.is_superadmin():
            return True
        return request.user.organization is not None

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser or request.user.is_superadmin():
            return True
        # Object must have organization field
        if hasattr(obj, 'organization'):
            return obj.organization == request.user.organization
        # For objects that belong to user's org through duty
        if hasattr(obj, 'duty') and hasattr(obj.duty, 'organization'):
            return obj.duty.organization == request.user.organization
        return False

class IsOrgEmployee(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_employee():
            return request.user.organization_id is not None
        return False


def get_user_permissions(groups):
    permissions, result = [], []
    for group in groups:
        for permission in group.permissions.all():
            code_name = permission.codename.split('_')
            permissions.append({
                "model": code_name[1].upper(),
                "permission": code_name[0].upper()
            })

    permissions = sorted(permissions, key=itemgetter('model'))

    for key, value in groupby(permissions, key=itemgetter('model')):
        result.append({key: [val["permission"] for val in value]})

    return result
