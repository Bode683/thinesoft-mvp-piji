"""
Platform-level permission classes.

These permissions check platform_admin realm role from Keycloak.
This is the ONLY permission that checks realm roles - tenant permissions
should use TenantMembership instead.
"""
from rest_framework.permissions import BasePermission


class IsPlatformAdmin(BasePermission):
    """
    User has platform_admin realm role OR is Django superuser.

    This is the ONLY permission that checks realm roles directly.
    All other tenant-scoped permissions use TenantMembership.

    Usage:
    - Cross-tenant administration
    - Creating new tenants
    - Viewing all tenants
    - System-wide configuration
    """
    message = "Platform administrator access required."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Django superuser always has platform admin access
        if request.user.is_superuser:
            return True

        # Check for platform_admin realm role from JWT
        if hasattr(request, 'auth_context'):
            return request.auth_context.is_platform_admin()

        return False


class IsPlatformAdminOrReadOnly(BasePermission):
    """
    Platform admin for write operations, authenticated for read.

    Useful for resources that can be viewed by any authenticated user
    but only modified by platform admins.
    """
    message = "Platform administrator access required for this action."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Allow read operations for any authenticated user
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True

        # Require platform admin for write operations
        if request.user.is_superuser:
            return True

        if hasattr(request, 'auth_context'):
            return request.auth_context.is_platform_admin()

        return False
