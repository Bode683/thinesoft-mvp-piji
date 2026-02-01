"""
Generic authentication permissions.
"""
from rest_framework.permissions import BasePermission


class IsAuthenticatedWithContext(BasePermission):
    """
    User is authenticated and has an auth_context attached to the request.
    Use this when you need to access realm_roles or other JWT claims.
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and hasattr(request, 'auth_context')
        )


class HasKeycloakId(BasePermission):
    """
    User has a valid keycloak_id (is a Keycloak-managed user).
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return bool(request.user.keycloak_id)
