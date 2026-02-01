"""Tests for platform permissions."""
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from apps.platform.permissions import IsPlatformAdmin
from apps.identity.auth_context import AuthContext

User = get_user_model()


class PlatformPermissionsTest(TestCase):
    """Test platform permission classes."""

    def setUp(self):
        """Set up test data."""
        self.factory = RequestFactory()

        self.regular_user = User.objects.create_user(
            username="regular",
            email="regular@example.com"
        )
        self.superuser = User.objects.create_superuser(
            username="superuser",
            email="super@example.com",
            password="pass"
        )
        self.platform_admin = User.objects.create_user(
            username="platformadmin",
            email="platformadmin@example.com"
        )

    def test_is_platform_admin_allows_superuser(self):
        """Test IsPlatformAdmin allows Django superuser."""
        request = self.factory.get('/')
        request.user = self.superuser
        view = APIView()

        permission = IsPlatformAdmin()
        self.assertTrue(permission.has_permission(request, view))

    def test_is_platform_admin_allows_realm_role(self):
        """Test IsPlatformAdmin allows user with platform_admin realm role."""
        request = self.factory.get('/')
        request.user = self.platform_admin
        request.auth_context = AuthContext(
            keycloak_id="test-id",
            username="platformadmin",
            email="platformadmin@example.com",
            realm_roles=["platform_admin"]
        )
        view = APIView()

        permission = IsPlatformAdmin()
        self.assertTrue(permission.has_permission(request, view))

    def test_is_platform_admin_denies_regular_user(self):
        """Test IsPlatformAdmin denies regular user."""
        request = self.factory.get('/')
        request.user = self.regular_user
        request.auth_context = AuthContext(
            keycloak_id="test-id",
            username="regular",
            email="regular@example.com",
            realm_roles=[]
        )
        view = APIView()

        permission = IsPlatformAdmin()
        self.assertFalse(permission.has_permission(request, view))

    def test_is_platform_admin_denies_unauthenticated(self):
        """Test IsPlatformAdmin denies unauthenticated user."""
        from django.contrib.auth.models import AnonymousUser

        request = self.factory.get('/')
        request.user = AnonymousUser()
        view = APIView()

        permission = IsPlatformAdmin()
        self.assertFalse(permission.has_permission(request, view))

    def test_is_platform_admin_without_auth_context(self):
        """Test IsPlatformAdmin when auth_context is not present."""
        request = self.factory.get('/')
        request.user = self.regular_user
        # No auth_context attached
        view = APIView()

        permission = IsPlatformAdmin()
        self.assertFalse(permission.has_permission(request, view))

    def test_is_platform_admin_with_other_realm_roles(self):
        """Test IsPlatformAdmin denies user with other realm roles."""
        request = self.factory.get('/')
        request.user = self.regular_user
        request.auth_context = AuthContext(
            keycloak_id="test-id",
            username="regular",
            email="regular@example.com",
            realm_roles=["some_other_role", "another_role"]
        )
        view = APIView()

        permission = IsPlatformAdmin()
        self.assertFalse(permission.has_permission(request, view))
