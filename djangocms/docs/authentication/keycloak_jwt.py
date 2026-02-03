"""
Keycloak JWT Authentication for Django REST Framework

This module provides JWT token validation for tokens issued by Keycloak.
It acts as a resource server, validating tokens issued to the frontend client.
"""

import jwt
from jwt import PyJWKClient
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class KeycloakJWTAuthentication(BaseAuthentication):
    """
    JWT Authentication for Keycloak tokens.

    Validates tokens issued to the frontend client (wiwebb-web-client)
    using Keycloak's JWKS endpoint for signature verification.

    This is separate from the backend service account (djangocms-client)
    which is used for admin operations only.
    """

    def __init__(self):
        # Initialize JWKS client with caching
        jwks_url = (
            f"{settings.KEYCLOAK_SERVER_URL}/realms/{settings.KEYCLOAK_REALM}"
            f"/protocol/openid-connect/certs"
        )

        self.jwks_client = PyJWKClient(
            jwks_url,
            cache_keys=True,
            max_cached_keys=16,
            cache_jwk_set=True,
            lifespan=360,  # Cache JWKS for 6 minutes
        )

        logger.info(f"Keycloak JWT Authentication initialized with JWKS URL: {jwks_url}")

    def authenticate(self, request):
        """
        Authenticate the request using Keycloak JWT token.

        Returns:
            tuple: (user, token_payload) if authentication succeeds
            None: if no authentication is attempted

        Raises:
            AuthenticationFailed: if authentication fails
        """
        # Extract token from Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith('Bearer '):
            return None

        token = auth_header.split(' ')[1]

        try:
            # Validate and decode token
            payload = self._validate_token(token)

            # Get or create Django user from token
            user = self._get_or_create_user(payload)

            logger.debug(
                f"User {user.username} authenticated successfully "
                f"(Keycloak ID: {payload.get('sub')})"
            )

            return (user, payload)

        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {str(e)}")
            raise AuthenticationFailed(f'Invalid token: {str(e)}')
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}", exc_info=True)
            raise AuthenticationFailed(f'Authentication failed: {str(e)}')

    def _validate_token(self, token):
        """
        Validate JWT token signature and claims.

        Args:
            token (str): JWT token string

        Returns:
            dict: Decoded token payload

        Raises:
            jwt.InvalidTokenError: if token is invalid
        """
        # Get signing key from JWKS
        signing_key = self.jwks_client.get_signing_key_from_jwt(token)

        # Expected issuer
        issuer = f"{settings.KEYCLOAK_SERVER_URL}/realms/{settings.KEYCLOAK_REALM}"

        # Accepted audiences (can be a string or list)
        audiences = settings.KEYCLOAK_ACCEPTED_AUDIENCES
        if isinstance(audiences, str):
            audiences = [audiences]

        # Decode and validate token
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=audiences,  # PyJWT accepts list - validates if ANY match
            issuer=issuer,
            options={
                "verify_signature": True,
                "verify_aud": True,
                "verify_iat": True,
                "verify_exp": True,
                "verify_iss": True,
                "require": ["exp", "iat", "sub", "iss", "aud"],
            }
        )

        logger.debug(f"Token validated for subject: {payload.get('sub')}")
        return payload

    def _get_or_create_user(self, payload):
        """
        Get or create Django user from Keycloak token payload.

        Args:
            payload (dict): Decoded JWT payload

        Returns:
            User: Django user instance
        """
        keycloak_id = payload.get('sub')
        username = payload.get('preferred_username')
        email = payload.get('email', '')

        if not username:
            raise AuthenticationFailed('Token missing preferred_username claim')

        # Try to get user by username first
        try:
            user = User.objects.get(username=username)

            # Update user info if changed
            updated = False
            if user.email != email and email:
                user.email = email
                updated = True

            first_name = payload.get('given_name', '')
            if user.first_name != first_name and first_name:
                user.first_name = first_name
                updated = True

            last_name = payload.get('family_name', '')
            if user.last_name != last_name and last_name:
                user.last_name = last_name
                updated = True

            if updated:
                user.save()
                logger.info(f"Updated user info for {username}")

        except User.DoesNotExist:
            # Create new user
            user = User.objects.create(
                username=username,
                email=email,
                first_name=payload.get('given_name', ''),
                last_name=payload.get('family_name', ''),
            )
            logger.info(f"Created new user: {username} (Keycloak ID: {keycloak_id})")

        # Attach Keycloak metadata to user object (not saved to DB)
        # This can be used in views for authorization decisions
        user.keycloak_id = keycloak_id
        user.keycloak_token = payload
        user.keycloak_roles = self._extract_roles(payload)
        user.keycloak_groups = payload.get('groups', [])

        return user

    def _extract_roles(self, payload):
        """
        Extract roles from token payload.

        Supports both realm roles and client roles.

        Args:
            payload (dict): Token payload

        Returns:
            list: List of role names
        """
        roles = []

        # Realm roles
        realm_access = payload.get('realm_access', {})
        roles.extend(realm_access.get('roles', []))

        # Client roles (if needed)
        resource_access = payload.get('resource_access', {})
        for client, access in resource_access.items():
            client_roles = access.get('roles', [])
            # Prefix client roles with client name
            roles.extend([f"{client}:{role}" for role in client_roles])

        return roles

    def authenticate_header(self, request):
        """
        Return WWW-Authenticate header for 401 responses.
        """
        return 'Bearer realm="Keycloak"'
