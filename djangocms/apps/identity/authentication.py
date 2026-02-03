"""
JWT authentication with role extraction using PyJWT.
NO SessionAuthentication for API - JWT only.
"""
import logging
from typing import Optional, Tuple
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.request import Request
import jwt
from jwt import PyJWKClient

from .auth_context import AuthContext

logger = logging.getLogger(__name__)
User = get_user_model()


class KeycloakJWTAuthentication(BaseAuthentication):
    """
    Keycloak JWT authentication using PyJWT signature validation.

    - Validates JWT signature using Keycloak's JWKS
    - Extracts realm_roles and client_roles into AuthContext
    - Syncs user with keycloak_id
    - Attaches auth_context to request
    - NO introspection - pure JWT validation
    """

    def __init__(self):
        """Initialize PyJWKClient with Keycloak JWKS URL."""
        super().__init__()
        self.jwks_client = PyJWKClient(
            settings.KEYCLOAK_JWKS_URL,
            cache_keys=True,      # Cache signing keys
            max_cached_keys=16,   # Max keys to cache
            cache_jwk_set=True,   # Cache entire JWKS
            lifespan=3600,        # Cache for 1 hour
        )

    def authenticate(self, request: Request) -> Optional[Tuple[User, AuthContext]]:
        """
        Authenticate the request and return a tuple of (user, auth_context).

        Steps:
        1. Extract Bearer token from Authorization header
        2. Validate JWT signature using JWKS
        3. Verify claims (audience, issuer, expiration)
        4. Build AuthContext from token claims
        5. Get or create Django user
        6. Sync user fields from token
        7. Attach auth_context to request

        Returns:
            Tuple of (User, AuthContext) or None if no auth header
        """
        # Extract token from header
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith('Bearer '):
            return None

        token = auth_header.split(' ')[1]

        # Validate JWT and extract claims
        try:
            token_data = self._validate_token(token)
        except AuthenticationFailed:
            raise
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            raise AuthenticationFailed('Invalid token')

        # Build auth context from token
        auth_context = self._build_auth_context(token_data)

        # Get or create user
        user = self._get_or_create_user(auth_context)

        # Sync user with Keycloak data (no role sync)
        user = self._sync_user(user, auth_context)

        # Attach to request for use in views/permissions
        request.auth_context = auth_context

        return (user, auth_context)

    def _validate_token(self, token: str) -> dict:
        """
        Validate JWT token signature and claims.

        Args:
            token: Raw JWT token string

        Returns:
            Decoded token payload (dict)

        Raises:
            AuthenticationFailed: If token is invalid
        """
        try:
            # Get signing key from JWKS
            signing_key = self.jwks_client.get_signing_key_from_jwt(token)

            # Decode and validate
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=settings.KEYCLOAK_FRONTEND_CLIENT_ID,  # wiwebb-web-client
                issuer=settings.KEYCLOAK_ISSUER,
                options={
                    "verify_signature": settings.KEYCLOAK_VERIFY_SIGNATURE,
                    "verify_aud": settings.KEYCLOAK_VERIFY_AUDIENCE,
                    "verify_exp": settings.KEYCLOAK_VERIFY_EXPIRATION,
                    "verify_iss": settings.KEYCLOAK_VERIFY_ISSUER,
                }
            )

            return payload

        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            raise AuthenticationFailed('Token has expired')
        except jwt.InvalidAudienceError:
            logger.warning("Token audience mismatch")
            raise AuthenticationFailed('Invalid token audience')
        except jwt.InvalidIssuerError:
            logger.warning("Token issuer mismatch")
            raise AuthenticationFailed('Invalid token issuer')
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            raise AuthenticationFailed(f'Invalid token: {str(e)}')
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            raise AuthenticationFailed('Token validation failed')

    def _get_or_create_user(self, ctx: AuthContext) -> User:
        """
        Get or create Django user from AuthContext.

        Uses username from token (preferred_username claim).
        Creates user if doesn't exist.

        Args:
            ctx: AuthContext with user data from token

        Returns:
            User instance
        """
        try:
            user = User.objects.get(username=ctx.username)
        except User.DoesNotExist:
            # Create new user from token data
            user = User.objects.create_user(
                username=ctx.username,
                email=ctx.email,
                first_name=ctx.first_name,
                last_name=ctx.last_name,
            )
            logger.info(f"Created new user from Keycloak: {ctx.username}")

        return user

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

        # Extract client roles (use backend client ID, not frontend)
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
