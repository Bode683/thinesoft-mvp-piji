"""Tests for AuthContext dataclass."""
from django.test import TestCase
from apps.identity.auth_context import AuthContext


class AuthContextTest(TestCase):
    """Test AuthContext functionality."""

    def test_auth_context_creation(self):
        """Test creating AuthContext with minimal data."""
        ctx = AuthContext(
            keycloak_id="550e8400-e29b-41d4-a716-446655440000",
            username="testuser",
            email="test@example.com"
        )

        self.assertEqual(ctx.keycloak_id, "550e8400-e29b-41d4-a716-446655440000")
        self.assertEqual(ctx.username, "testuser")
        self.assertEqual(ctx.email, "test@example.com")
        self.assertEqual(ctx.realm_roles, [])
        self.assertEqual(ctx.client_roles, [])

    def test_auth_context_with_roles(self):
        """Test AuthContext with realm and client roles."""
        ctx = AuthContext(
            keycloak_id="test-id",
            username="admin",
            email="admin@example.com",
            realm_roles=["platform_admin"],
            client_roles=["api_access"]
        )

        self.assertEqual(ctx.realm_roles, ["platform_admin"])
        self.assertEqual(ctx.client_roles, ["api_access"])

    def test_has_realm_role(self):
        """Test has_realm_role method."""
        ctx = AuthContext(
            keycloak_id="test-id",
            username="user",
            email="user@example.com",
            realm_roles=["platform_admin", "user"]
        )

        self.assertTrue(ctx.has_realm_role("platform_admin"))
        self.assertTrue(ctx.has_realm_role("user"))
        self.assertFalse(ctx.has_realm_role("nonexistent"))

    def test_is_platform_admin(self):
        """Test is_platform_admin method."""
        # Platform admin
        admin_ctx = AuthContext(
            keycloak_id="admin-id",
            username="admin",
            email="admin@example.com",
            realm_roles=["platform_admin"]
        )
        self.assertTrue(admin_ctx.is_platform_admin())

        # Regular user
        user_ctx = AuthContext(
            keycloak_id="user-id",
            username="user",
            email="user@example.com",
            realm_roles=[]
        )
        self.assertFalse(user_ctx.is_platform_admin())

    def test_raw_token_storage(self):
        """Test that raw token is stored."""
        token = {
            "sub": "test-id",
            "email": "test@example.com",
            "exp": 1234567890
        }
        ctx = AuthContext(
            keycloak_id="test-id",
            username="test",
            email="test@example.com",
            raw_token=token
        )

        self.assertEqual(ctx.raw_token, token)
        self.assertEqual(ctx.raw_token["exp"], 1234567890)
