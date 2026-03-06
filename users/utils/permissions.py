from itertools import groupby
from operator import itemgetter

from rest_framework.permissions import BasePermission


def _org_in_district(obj, district_id):
    """obj.organization_id ning districtini tekshiradi."""
    org_id = getattr(obj, 'organization_id', None)
    if org_id is None:
        return False
    from directory.models import Organization
    return Organization.objects.filter(pk=org_id, district_id=district_id).exists()


class IsSuperAdmin(BasePermission):
    """Full system access. Superuser flag OR SUPER_ADMIN role."""
    message = "Faqat super admin bu amalni bajarishi mumkin."

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        return request.user.is_super_admin()

    def has_object_permission(self, request, view, obj):
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
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.is_super_admin():
            return True
        org_id = getattr(obj, 'organization_id', None)
        return org_id is not None and org_id == request.user.organization_id


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

    def has_object_permission(self, request, view, obj):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.is_super_admin():
            return True
        return (
            request.user.is_collector()
            and request.user.district_id is not None
            and _org_in_district(obj, request.user.district_id)
        )


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

    def has_object_permission(self, request, view, obj):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.is_super_admin():
            return True
        return (
            request.user.is_district_admin()
            and request.user.district_id is not None
            and _org_in_district(obj, request.user.district_id)
        )


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

    def has_object_permission(self, request, view, obj):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.is_super_admin():
            return True
        return (
            (request.user.is_collector() or request.user.is_district_admin())
            and request.user.district_id is not None
            and _org_in_district(obj, request.user.district_id)
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
