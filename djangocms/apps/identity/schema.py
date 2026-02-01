"""
OpenAPI schema extensions for identity app.
"""
from drf_spectacular.extensions import OpenApiAuthenticationExtension
from drf_spectacular.plumbing import build_bearer_security_scheme_object


class KeycloakJWTAuthenticationScheme(OpenApiAuthenticationExtension):
    """
    Custom OpenAPI authentication scheme for KeycloakJWTAuthentication.

    This extension properly documents our custom JWT authentication in the OpenAPI schema,
    including details about the AuthContext that gets attached to requests.
    """
    target_class = "apps.identity.authentication.KeycloakJWTAuthentication"
    name = "KeycloakJWT"

    def get_security_definition(self, auto_schema):
        """
        Return the security definition for Keycloak JWT authentication.
        """
        return build_bearer_security_scheme_object(
            header_name="Authorization",
            token_prefix="Bearer",
            bearer_format="JWT",
        )
