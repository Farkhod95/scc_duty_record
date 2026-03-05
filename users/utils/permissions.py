from itertools import groupby
from operator import itemgetter

from rest_framework.permissions import BasePermission


class IsSuperAdmin(BasePermission):
    """Full system access. Superuser flag OR SUPER_ADMIN role."""
    message = "Faqat super admin bu amalni bajarishi mumkin."

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        return request.user.is_super_admin()


class IsOfficer(BasePermission):
    """
    Org-level: creates and submits duties for their own organization.
    SuperAdmin also passes.
    """
    message = "Faqat tashkilot masul xodimi bu amalni bajarishi mumkin."

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.is_super_admin():
            return True
        return request.user.is_officer() and request.user.organization_id is not None

    def has_object_permission(self, request, view, obj):
        if request.user.is_super_admin():
            return True
        if hasattr(obj, 'organization_id'):
            return obj.organization_id == request.user.organization_id
        return False


class IsCollector(BasePermission):
    """
    District-level: sees all submitted duties in their district, first approval.
    SuperAdmin also passes.
    """
    message = "Faqat tuman yig'uvchisi bu amalni bajarishi mumkin."

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.is_super_admin():
            return True
        return request.user.is_collector() and request.user.district_id is not None


class IsDistrictAdmin(BasePermission):
    """
    District-level: final approval authority.
    SuperAdmin also passes.
    """
    message = "Faqat tuman admin bu amalni bajarishi mumkin."

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.is_super_admin():
            return True
        return request.user.is_district_admin() and request.user.district_id is not None


class IsDistrictLevel(BasePermission):
    """
    Collector OR DistrictAdmin (or SuperAdmin).
    Used for read-only district views shared by both roles.
    """
    message = "Tuman darajasidagi ruxsat talab etiladi."

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.is_super_admin():
            return True
        return (
            (request.user.is_collector() or request.user.is_district_admin())
            and request.user.district_id is not None
        )


# ---------------------------------------------------------------------------
# Backward-compatibility aliases — old monitoring views, replaced in Etap 2+
# ---------------------------------------------------------------------------
IsOrgAdmin = IsOfficer
IsManager = IsOfficer
IsOrgEmployee = IsOfficer
IsOrgMember = IsOfficer


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
