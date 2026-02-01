"""Tests for tenant services (business logic)."""
from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.tenants.models import Tenant, TenantMembership
from apps.tenants import services

User = get_user_model()


class TenantServicesTest(TestCase):
    """Test tenant service layer."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="owner",
            email="owner@example.com"
        )

    def test_create_tenant(self):
        """Test create_tenant creates tenant and owner membership."""
        tenant = services.create_tenant(
            name="New Tenant",
            slug="new-tenant",
            owner_user=self.user
        )

        # Verify tenant created
        self.assertEqual(tenant.name, "New Tenant")
        self.assertEqual(tenant.slug, "new-tenant")

        # Verify owner membership created
        membership = TenantMembership.objects.get(
            user=self.user,
            tenant=tenant
        )
        self.assertEqual(membership.role, TenantMembership.Role.OWNER)

    def test_create_tenant_with_optional_fields(self):
        """Test create_tenant with optional fields."""
        tenant = services.create_tenant(
            name="Full Tenant",
            slug="full-tenant",
            owner_user=self.user,
            description="Full description",
            email="contact@fulltenant.com",
            url="https://fulltenant.com"
        )

        self.assertEqual(tenant.description, "Full description")
        self.assertEqual(tenant.email, "contact@fulltenant.com")
        self.assertEqual(tenant.url, "https://fulltenant.com")

    def test_add_member_creates_new_membership(self):
        """Test add_member creates new membership."""
        tenant = Tenant.objects.create(name="Test Tenant", slug="test")
        new_user = User.objects.create_user(
            username="newuser",
            email="new@example.com"
        )

        membership, created = services.add_member(
            tenant=tenant,
            user=new_user,
            role=TenantMembership.Role.ADMIN
        )

        self.assertTrue(created)
        self.assertEqual(membership.user, new_user)
        self.assertEqual(membership.tenant, tenant)
        self.assertEqual(membership.role, TenantMembership.Role.ADMIN)

    def test_add_member_does_not_duplicate(self):
        """Test add_member doesn't create duplicate membership."""
        tenant = Tenant.objects.create(name="Test Tenant", slug="test")

        # First add
        membership1, created1 = services.add_member(
            tenant=tenant,
            user=self.user
        )
        self.assertTrue(created1)

        # Second add (should return existing)
        membership2, created2 = services.add_member(
            tenant=tenant,
            user=self.user
        )
        self.assertFalse(created2)
        self.assertEqual(membership1.id, membership2.id)

    def test_add_member_default_role(self):
        """Test add_member uses MEMBER as default role."""
        tenant = Tenant.objects.create(name="Test Tenant", slug="test")
        new_user = User.objects.create_user(
            username="member",
            email="member@example.com"
        )

        membership, _ = services.add_member(tenant=tenant, user=new_user)
        self.assertEqual(membership.role, TenantMembership.Role.MEMBER)

    def test_can_user_manage_tenant_owner(self):
        """Test can_user_manage_tenant returns True for owner."""
        tenant = services.create_tenant(
            name="Test Tenant",
            slug="test",
            owner_user=self.user
        )

        self.assertTrue(services.can_user_manage_tenant(self.user, tenant))

    def test_can_user_manage_tenant_admin(self):
        """Test can_user_manage_tenant returns True for admin."""
        tenant = Tenant.objects.create(name="Test Tenant", slug="test")
        TenantMembership.objects.create(
            user=self.user,
            tenant=tenant,
            role=TenantMembership.Role.ADMIN
        )

        self.assertTrue(services.can_user_manage_tenant(self.user, tenant))

    def test_can_user_manage_tenant_member(self):
        """Test can_user_manage_tenant returns False for regular member."""
        tenant = Tenant.objects.create(name="Test Tenant", slug="test")
        TenantMembership.objects.create(
            user=self.user,
            tenant=tenant,
            role=TenantMembership.Role.MEMBER
        )

        self.assertFalse(services.can_user_manage_tenant(self.user, tenant))

    def test_can_user_manage_tenant_not_member(self):
        """Test can_user_manage_tenant returns False for non-member."""
        tenant = Tenant.objects.create(name="Test Tenant", slug="test")

        self.assertFalse(services.can_user_manage_tenant(self.user, tenant))
