"""
Keycloak authentication backend for OAuth2-Proxy header-based authentication.

This module provides the KeycloakRemoteUserBackend which authenticates users
based on headers forwarded by OAuth2-Proxy after successful Keycloak authentication.
"""

from django.contrib.auth.backends import RemoteUserBackend
from django.contrib.auth import get_user_model

User = get_user_model()


class KeycloakRemoteUserBackend(RemoteUserBackend):
    """
    Authentication backend for OAuth2-Proxy forwarded headers.

    This backend is used in conjunction with OAuth2ProxyRemoteUserMiddleware
    to authenticate users based on headers forwarded by OAuth2-Proxy after
    successful Keycloak authentication.

    Headers used:
    - X-Auth-Request-Email: User's email (used as username)
    - X-Auth-Request-Preferred-Username: Keycloak preferred username
    - X-Auth-Request-Given-Name: User's first name
    - X-Auth-Request-Family-Name: User's last name
    - X-Auth-Request-Groups: Comma-separated list of Keycloak groups
    """

    create_unknown_user = True  # Auto-create users on first login

    def configure_user(self, request, user, created=False):
        """
        Called when a user is created or updated.
        Sync user attributes from OAuth2-Proxy headers.

        Args:
            request: HttpRequest with META containing X-Auth-Request-* headers
            user: User instance
            created: Boolean indicating if user was just created

        Returns:
            User instance
        """
        # Sync user attributes from headers
        email = request.META.get('HTTP_X_AUTH_REQUEST_EMAIL', '')
        given_name = request.META.get('HTTP_X_AUTH_REQUEST_GIVEN_NAME', '')
        family_name = request.META.get('HTTP_X_AUTH_REQUEST_FAMILY_NAME', '')
        groups_raw = request.META.get('HTTP_X_AUTH_REQUEST_GROUPS', '')

        # Parse groups (comma-separated)
        groups = [g.strip() for g in groups_raw.split(',') if g.strip()]

        # Update user fields
        user.email = email
        user.first_name = given_name
        user.last_name = family_name

        # Map Keycloak groups to Django User roles (if you have a role field)
        # Example implementation (uncomment if you have a role field):
        # user.role = self._map_groups_to_role(groups)

        user.save()

        # Sync groups/tenants (optional - implement if you have a Tenant model)
        # self._sync_user_tenants(user, groups)

        return user

    def clean_username(self, username, request):
        """
        Clean the username (email) before creating the user.

        Args:
            username: Raw username from header
            request: HttpRequest

        Returns:
            Cleaned username
        """
        # Use email as username, normalized to lowercase
        return username.lower().strip()

    def _map_groups_to_role(self, groups):
        """
        Map Keycloak groups to Django User role.
        Priority: SUPERADMIN > ADMIN > TENANT_OWNER > SUBSCRIBER

        Args:
            groups: List of Keycloak group paths (e.g., ['/Acme-Corp', '/Admin'])

        Returns:
            String role name
        """
        # Role priority mapping (uncomment if you have a role field)
        # role_priority = {
        #     'SUPERADMIN': 4,
        #     'ADMIN': 3,
        #     'TENANT_OWNER': 2,
        #     'SUBSCRIBER': 1
        # }
        #
        # # Extract role from group names
        # detected_roles = []
        # for group in groups:
        #     group_name = group.strip('/')
        #     if group_name.upper() in role_priority:
        #         detected_roles.append(group_name.upper())
        #
        # # Return highest priority role
        # if detected_roles:
        #     return max(detected_roles, key=lambda r: role_priority.get(r, 0))
        #
        # return 'SUBSCRIBER'  # Default role
        pass

    def _sync_user_tenants(self, user, groups):
        """
        Sync Keycloak groups to Django Tenant model.

        Args:
            user: User instance
            groups: List of Keycloak group paths (e.g., ['/Acme-Corp'])
        """
        # Optional implementation for multi-tenancy
        # from your_app.models import Tenant
        #
        # for group_path in groups:
        #     # Extract tenant name from group path (e.g., '/Acme-Corp' -> 'Acme-Corp')
        #     tenant_name = group_path.strip('/')
        #
        #     if tenant_name and not tenant_name.upper() in ['SUPERADMIN', 'ADMIN', 'TENANT_OWNER', 'SUBSCRIBER']:
        #         # Create or get tenant
        #         tenant, created = Tenant.objects.get_or_create(
        #             name=tenant_name,
        #             defaults={'slug': tenant_name.lower().replace(' ', '-')}
        #         )
        #
        #         # Add user to tenant (M2M relationship)
        #         user.tenants.add(tenant)
        pass
