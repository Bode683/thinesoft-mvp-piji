"""
Tenant-aware permission classes.

These permissions check tenant-scoped roles from TenantMembership,
NOT from Keycloak realm roles.
"""
from rest_framework.permissions import BasePermission

from .models import TenantMembership


class IsTenantMember(BasePermission):
    """
    User is a member of the tenant being accessed.

    Expects the view to have a `get_tenant()` method or
    the object to have a `tenant` attribute.
    """
    message = "You must be a member of this tenant."

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True

        # Get tenant from object
        tenant = getattr(obj, 'tenant', obj)
        tenant_id = tenant.id if hasattr(tenant, 'id') else tenant

        return TenantMembership.objects.filter(
            user=request.user,
            tenant_id=tenant_id
        ).exists()


class IsTenantOwner(BasePermission):
    """
    User is owner of the tenant via TenantMembership.

    NOT based on realm role - this is tenant-scoped authorization.
    """
    message = "You must be the owner of this tenant."

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True

        # Get tenant from object
        tenant = getattr(obj, 'tenant', obj)
        tenant_id = tenant.id if hasattr(tenant, 'id') else tenant

        return TenantMembership.objects.filter(
            user=request.user,
            tenant_id=tenant_id,
            role=TenantMembership.Role.OWNER
        ).exists()


class IsTenantAdmin(BasePermission):
    """
    User is owner or admin of the tenant.

    Can perform administrative actions within the tenant.
    """
    message = "You must be an admin or owner of this tenant."

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True

        # Get tenant from object
        tenant = getattr(obj, 'tenant', obj)
        tenant_id = tenant.id if hasattr(tenant, 'id') else tenant

        return TenantMembership.objects.filter(
            user=request.user,
            tenant_id=tenant_id,
            role__in=[TenantMembership.Role.OWNER, TenantMembership.Role.ADMIN]
        ).exists()


class IsTenantMemberOrPlatformAdmin(BasePermission):
    """
    User is a tenant member OR has platform_admin realm role.

    Useful for endpoints that platform admins can access across all tenants.
    """
    message = "You must be a member of this tenant or a platform admin."

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True

        # Check for platform_admin realm role
        if hasattr(request, 'auth_context'):
            if request.auth_context.is_platform_admin():
                return True

        # Check for tenant membership
        tenant = getattr(obj, 'tenant', obj)
        tenant_id = tenant.id if hasattr(tenant, 'id') else tenant

        return TenantMembership.objects.filter(
            user=request.user,
            tenant_id=tenant_id
        ).exists()
