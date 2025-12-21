from rest_framework.permissions import BasePermission, SAFE_METHODS
from django.contrib.auth.models import Group


def in_group(user, name: str) -> bool:
    try:
        return user.groups.filter(name=name).exists()
    except Exception:
        return False


class IsSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_superuser)


class IsPlatformAdmin(BasePermission):
    """Platform-level admin (not tenant). We define this as is_staff + in Admin group."""

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_staff and in_group(user, "Admin"))


class IsSuperAdminOrPlatformAdmin(BasePermission):
    """Allow if user is either SuperAdmin or in Platform Admin group (and staff)."""

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        return bool(user.is_superuser or (user.is_staff and in_group(user, "Admin")))


class IsTenantOwner(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and getattr(user, "role", None) == user.Roles.TENANT_OWNER)


class IsSameTenantOrSuperAdmin(BasePermission):
    """Object-level check that either user is superadmin or object's tenant matches user's tenant.
    Expects obj to have a `tenant` attribute (User or tenant-bound model).
    """

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if user.is_superuser:
            return True
        obj_tenant = getattr(obj, "tenant", None)
        return bool(obj_tenant and user.tenant_id and obj_tenant_id(obj) == user.tenant_id)


def obj_tenant_id(obj):
    t = getattr(obj, "tenant", None)
    return getattr(t, "id", None)


class CanManageTenantUsers(BasePermission):
    """TenantOwner can manage users within their own tenant; SuperAdmin/Admin unrestricted."""

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if user.is_superuser or (user.is_staff and in_group(user, "Admin")):
            return True
        # Tenant owner limited management
        return getattr(user, "role", None) == user.Roles.TENANT_OWNER

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.is_superuser or (user.is_staff and in_group(user, "Admin")):
            return True
        # Tenant owner can only manage users in their tenant
        return getattr(obj, "tenant_id", None) == getattr(user, "tenant_id", None)
