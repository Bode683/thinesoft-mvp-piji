"""
OAuth2-Proxy authentication middleware.

This module provides middleware to authenticate users via OAuth2-Proxy forwarded headers
after successful Keycloak authentication.
"""

from django.contrib.auth.middleware import RemoteUserMiddleware
from django.conf import settings


class OAuth2ProxyRemoteUserMiddleware(RemoteUserMiddleware):
    """
    Middleware to authenticate users via OAuth2-Proxy forwarded headers.

    This uses Django's built-in RemoteUserMiddleware pattern, which:
    - Automatically logs in users when the header is present
    - Logs out users if the header username changes
    - Works with RemoteUserBackend for user creation/sync

    OAuth2-Proxy forwards these headers after successful Keycloak authentication:
    - X-Auth-Request-Email (used as username)
    - X-Auth-Request-Preferred-Username
    - X-Auth-Request-Given-Name
    - X-Auth-Request-Family-Name
    - X-Auth-Request-Groups

    Security notes:
    - Only trust headers from internal network (Traefik/OAuth2-Proxy)
    - API paths (/api/*) skip this middleware (they use JWT authentication)
    - In dev mode, allows local admin login without OAuth2-Proxy
    """

    # The header containing the authenticated username/email
    header = 'HTTP_X_AUTH_REQUEST_EMAIL'

    # Force logout if the header is not present (strict mode)
    # Set to False for dev to allow local admin login
    force_logout_if_no_header = False

    def process_request(self, request):
        """
        Override to skip authentication for API paths (which use JWT).

        Args:
            request: HttpRequest

        Returns:
            None or HttpResponse
        """
        # Skip OAuth2-Proxy auth for API endpoints (they use JWT)
        if request.path.startswith('/api/'):
            return

        # Dev mode: Skip if accessing from localhost without headers (allows createsuperuser login)
        if settings.DEBUG:
            remote_user = request.META.get(self.header)
            remote_addr = request.META.get('REMOTE_ADDR', '')

            # Allow local access without OAuth2-Proxy headers
            if not remote_user and remote_addr in ['127.0.0.1', 'localhost', '::1']:
                return

        # Call parent RemoteUserMiddleware logic
        return super().process_request(request)
