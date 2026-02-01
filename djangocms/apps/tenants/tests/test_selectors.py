"""Tests for tenant selectors (read-only queries)."""
from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.tenants.models import Tenant, TenantMembership
from apps.tenants import selectors

User = get_user_model()


class TenantSelectorsTest(TestCase):
    """Test tenant selector functions."""

    def setUp(self):
        """Set up test data."""
        self.user1 = User.objects.create_user(
            username="user1",
            email="user1@example.com"
        )
        self.user2 = User.objects.create_user(
            username="user2",
            email="user2@example.com"
        )

        self.tenant1 = Tenant.objects.create(name="Tenant 1", slug="tenant-1")
        self.tenant2 = Tenant.objects.create(name="Tenant 2", slug="tenant-2")

        # user1 is member of both tenants
        TenantMembership.objects.create(
            user=self.user1,
            tenant=self.tenant1,
            role=TenantMembership.Role.OWNER
        )
        TenantMembership.objects.create(
            user=self.user1,
            tenant=self.tenant2,
            role=TenantMembership.Role.MEMBER
        )

        # user2 is only member of tenant1
        TenantMembership.objects.create(
            user=self.user2,
            tenant=self.tenant1,
            role=TenantMembership.Role.ADMIN
        )

    def test_get_user_tenants(self):
        """Test get_user_tenants returns all user's tenants."""
        tenants = selectors.get_user_tenants(self.user1)
        self.assertEqual(tenants.count(), 2)
        self.assertIn(self.tenant1, tenants)
        self.assertIn(self.tenant2, tenants)

    def test_get_user_tenants_single_tenant(self):
        """Test get_user_tenants for user with single tenant."""
        tenants = selectors.get_user_tenants(self.user2)
        self.assertEqual(tenants.count(), 1)
        self.assertIn(self.tenant1, tenants)

    def test_get_user_tenants_no_tenants(self):
        """Test get_user_tenants for user with no tenants."""
        user3 = User.objects.create_user(
            username="user3",
            email="user3@example.com"
        )
        tenants = selectors.get_user_tenants(user3)
        self.assertEqual(tenants.count(), 0)

    def test_get_user_membership_exists(self):
        """Test get_user_membership when membership exists."""
        membership = selectors.get_user_membership(self.user1, self.tenant1)

        self.assertIsNotNone(membership)
        self.assertEqual(membership.user, self.user1)
        self.assertEqual(membership.tenant, self.tenant1)
        self.assertEqual(membership.role, TenantMembership.Role.OWNER)

    def test_get_user_membership_not_exists(self):
        """Test get_user_membership when membership doesn't exist."""
        membership = selectors.get_user_membership(self.user2, self.tenant2)
        self.assertIsNone(membership)

    def test_get_tenant_members(self):
        """Test get_tenant_members returns all members."""
        members = selectors.get_tenant_members(self.tenant1)

        self.assertEqual(members.count(), 2)
        member_users = [m.user for m in members]
        self.assertIn(self.user1, member_users)
        self.assertIn(self.user2, member_users)

    def test_get_tenant_members_single_member(self):
        """Test get_tenant_members for tenant with single member."""
        members = selectors.get_tenant_members(self.tenant2)

        self.assertEqual(members.count(), 1)
        self.assertEqual(members[0].user, self.user1)

    def test_get_tenant_members_select_related(self):
        """Test get_tenant_members uses select_related for efficiency."""
        members = selectors.get_tenant_members(self.tenant1)

        # Force evaluation of queryset
        members_list = list(members)

        # Accessing related user shouldn't trigger additional queries
        with self.assertNumQueries(0):
            for member in members_list:
                _ = member.user.email
