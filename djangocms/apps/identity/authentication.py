"""
JWT authentication with role extraction.
NO SessionAuthentication for API - JWT only.
"""
import logging
from typing import Optional, Tuple
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.request import Request
from drf_keycloak_auth.authentication import KeycloakAuthentication

from .auth_context import AuthContext

logger = logging.getLogger(__name__)
User = get_user_model()


class KeycloakJWTAuthentication(KeycloakAuthentication):
    """
    Enhanced Keycloak JWT authentication.

    - Extracts realm_roles and client_roles into AuthContext
    - Syncs user with keycloak_id
    - Attaches auth_context to request
    - NO role persistence in Django User model
    """

    def authenticate(self, request: Request) -> Optional[Tuple[User, AuthContext]]:
        """
        Authenticate the request and return a tuple of (user, auth_context).

        The auth_context contains:
        - keycloak_id
        - username
        - email
        - realm_roles (platform-level)
        - client_roles (client-specific)
        """
        result = super().authenticate(request)
        if result is None:
            return None

        user, token_data = result

        # Build auth context from token
        auth_context = self._build_auth_context(token_data)

        # Sync user with Keycloak data (no role sync)
        user = self._sync_user(user, auth_context)

        # Attach to request for use in views/permissions
        request.auth_context = auth_context

        return (user, auth_context)

    def _build_auth_context(self, token: dict) -> AuthContext:
        """
        Build AuthContext from JWT token claims.

        Extracts:
        - User identity from standard claims
        - Realm roles from realm_access.roles
        - Client roles from resource_access.<client_id>.roles
        """
        # Extract realm roles
        realm_access = token.get("realm_access", {})
        realm_roles = realm_access.get("roles", [])

        # Extract client roles
        client_id = getattr(settings, "KEYCLOAK_CLIENT_ID", "")
        resource_access = token.get("resource_access", {})
        client_access = resource_access.get(client_id, {})
        client_roles = client_access.get("roles", [])

        return AuthContext(
            keycloak_id=token.get("sub", ""),
            username=token.get("preferred_username", ""),
            email=token.get("email", ""),
            first_name=token.get("given_name", ""),
            last_name=token.get("family_name", ""),
            realm_roles=realm_roles,
            client_roles=client_roles,
            raw_token=token,
        )

    def _sync_user(self, user: User, ctx: AuthContext) -> User:
        """
        Sync user fields from Keycloak.

        IMPORTANT: NO role sync - roles are derived from:
        - auth_context.realm_roles (platform-level)
        - TenantMembership.role (tenant-scoped)
        """
        updated = False
        update_fields = []

        # Sync keycloak_id if not set
        if not user.keycloak_id and ctx.keycloak_id:
            try:
                import uuid
                user.keycloak_id = uuid.UUID(ctx.keycloak_id)
                update_fields.append('keycloak_id')
                updated = True
            except (ValueError, TypeError):
                logger.warning(f"Invalid keycloak_id format: {ctx.keycloak_id}")

        # Sync email
        if ctx.email and user.email != ctx.email:
            user.email = ctx.email
            update_fields.append('email')
            updated = True

        # Sync first name
        if ctx.first_name and user.first_name != ctx.first_name:
            user.first_name = ctx.first_name
            update_fields.append('first_name')
            updated = True

        # Sync last name
        if ctx.last_name and user.last_name != ctx.last_name:
            user.last_name = ctx.last_name
            update_fields.append('last_name')
            updated = True

        if updated:
            user.save(update_fields=update_fields)
            logger.info(f"Synced user {user.username} with Keycloak (fields: {update_fields})")

        return user
