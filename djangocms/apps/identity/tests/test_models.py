"""Tests for identity.User model."""
from django.test import TestCase
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()


class UserModelTest(TestCase):
    """Test User model behavior."""

    def test_user_creation_with_keycloak_id(self):
        """Test creating user with keycloak_id."""
        keycloak_id = uuid.uuid4()
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            keycloak_id=keycloak_id
        )

        self.assertEqual(user.keycloak_id, keycloak_id)
        self.assertEqual(user.email, "test@example.com")
        self.assertFalse(user.has_usable_password())

    def test_user_without_keycloak_id(self):
        """Test creating regular Django user without keycloak_id."""
        user = User.objects.create_user(
            username="regularuser",
            email="regular@example.com",
            password="testpass123"
        )

        self.assertIsNone(user.keycloak_id)
        self.assertTrue(user.has_usable_password())

    def test_keycloak_id_unique(self):
        """Test keycloak_id uniqueness constraint."""
        keycloak_id = uuid.uuid4()
        User.objects.create_user(
            username="user1",
            email="user1@example.com",
            keycloak_id=keycloak_id
        )

        # Should raise IntegrityError
        with self.assertRaises(Exception):
            User.objects.create_user(
                username="user2",
                email="user2@example.com",
                keycloak_id=keycloak_id
            )

    def test_user_profile_fields(self):
        """Test profile fields are saved correctly."""
        user = User.objects.create_user(
            username="profileuser",
            email="profile@example.com",
            phone_number="+1234567890",
            bio="Test bio",
            company="Test Company",
            location="Test City"
        )

        self.assertEqual(user.phone_number, "+1234567890")
        self.assertEqual(user.bio, "Test bio")
        self.assertEqual(user.company, "Test Company")
        self.assertEqual(user.location, "Test City")

    def test_no_role_field_in_user_model(self):
        """Verify User model does NOT have a role field."""
        user = User.objects.create_user(
            username="norole",
            email="norole@example.com"
        )

        # Should not have 'role' attribute
        self.assertFalse(hasattr(user, 'role'))

    def test_no_tenant_fk_in_user_model(self):
        """Verify User model does NOT have a tenant FK."""
        user = User.objects.create_user(
            username="notenant",
            email="notenant@example.com"
        )

        # Should not have 'tenant' or 'tenant_id' field
        self.assertFalse(hasattr(user, 'tenant'))
