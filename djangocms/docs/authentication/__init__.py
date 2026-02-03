"""
Authentication modules for Django CMS backend.
"""

from .keycloak_jwt import KeycloakJWTAuthentication

__all__ = ['KeycloakJWTAuthentication']
