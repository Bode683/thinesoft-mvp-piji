"""Tests for tenants models."""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from apps.tenants.models import Tenant, TenantMembership

User = get_user_model()


class TenantModelTest(TestCase):
    """Test Tenant model."""

    def test_tenant_creation(self):
        """Test creating a tenant."""
        tenant = Tenant.objects.create(
            name="Test Tenant",
            slug="test-tenant",
            description="Test description"
        )

        self.assertEqual(tenant.name, "Test Tenant")
        self.assertEqual(tenant.slug, "test-tenant")
        self.assertTrue(tenant.is_active)
        self.assertIsNotNone(tenant.uuid)

    def test_tenant_slug_unique(self):
        """Test tenant slug uniqueness."""
        Tenant.objects.create(name="Tenant 1", slug="same-slug")

        with self.assertRaises(IntegrityError):
            Tenant.objects.create(name="Tenant 2", slug="same-slug")

    def test_tenant_str_representation(self):
        """Test tenant string representation."""
        tenant = Tenant.objects.create(name="My Company", slug="my-company")
        self.assertEqual(str(tenant), "My Company")

    def test_tenant_ordering(self):
        """Test tenants are ordered by name."""
        Tenant.objects.create(name="Zebra Corp", slug="zebra")
        Tenant.objects.create(name="Alpha Inc", slug="alpha")

        tenants = list(Tenant.objects.all())
        self.assertEqual(tenants[0].name, "Alpha Inc")
        self.assertEqual(tenants[1].name, "Zebra Corp")


class TenantMembershipModelTest(TestCase):
    """Test TenantMembership model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com"
        )
        self.tenant = Tenant.objects.create(
            name="Test Tenant",
            slug="test-tenant"
        )

    def test_membership_creation(self):
        """Test creating a membership."""
        membership = TenantMembership.objects.create(
            user=self.user,
            tenant=self.tenant,
            role=TenantMembership.Role.OWNER
        )

        self.assertEqual(membership.user, self.user)
        self.assertEqual(membership.tenant, self.tenant)
        self.assertEqual(membership.role, TenantMembership.Role.OWNER)

    def test_membership_default_role(self):
        """Test default role is MEMBER."""
        membership = TenantMembership.objects.create(
            user=self.user,
            tenant=self.tenant
        )

        self.assertEqual(membership.role, TenantMembership.Role.MEMBER)

    def test_membership_unique_together(self):
        """Test user-tenant uniqueness constraint."""
        TenantMembership.objects.create(
            user=self.user,
            tenant=self.tenant,
            role=TenantMembership.Role.MEMBER
        )

        # Same user and tenant should fail
        with self.assertRaises(IntegrityError):
            TenantMembership.objects.create(
                user=self.user,
                tenant=self.tenant,
                role=TenantMembership.Role.ADMIN
            )

    def test_membership_str_representation(self):
        """Test membership string representation."""
        membership = TenantMembership.objects.create(
            user=self.user,
            tenant=self.tenant,
            role=TenantMembership.Role.OWNER
        )

        expected = f"{self.user.email} @ {self.tenant.slug} (owner)"
        self.assertEqual(str(membership), expected)

    def test_role_choices(self):
        """Test all role choices work."""
        for role_value, role_label in TenantMembership.Role.choices:
            membership = TenantMembership.objects.create(
                user=User.objects.create_user(
                    username=f"user_{role_value}",
                    email=f"{role_value}@example.com"
                ),
                tenant=self.tenant,
                role=role_value
            )
            self.assertEqual(membership.role, role_value)

    def test_multiple_tenants_per_user(self):
        """Test user can be member of multiple tenants."""
        tenant2 = Tenant.objects.create(name="Tenant 2", slug="tenant-2")

        TenantMembership.objects.create(
            user=self.user,
            tenant=self.tenant,
            role=TenantMembership.Role.OWNER
        )
        TenantMembership.objects.create(
            user=self.user,
            tenant=tenant2,
            role=TenantMembership.Role.MEMBER
        )

        self.assertEqual(self.user.tenant_memberships.count(), 2)

    def test_multiple_users_per_tenant(self):
        """Test tenant can have multiple members."""
        user2 = User.objects.create_user(
            username="user2",
            email="user2@example.com"
        )

        TenantMembership.objects.create(
            user=self.user,
            tenant=self.tenant,
            role=TenantMembership.Role.OWNER
        )
        TenantMembership.objects.create(
            user=user2,
            tenant=self.tenant,
            role=TenantMembership.Role.MEMBER
        )

        self.assertEqual(self.tenant.memberships.count(), 2)
