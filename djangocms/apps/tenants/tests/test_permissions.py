"""Tests for tenant permissions."""
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from apps.tenants.models import Tenant, TenantMembership
from apps.tenants.permissions import IsTenantMember, IsTenantOwner, IsTenantAdmin

User = get_user_model()


class TenantPermissionsTest(TestCase):
    """Test tenant permission classes."""

    def setUp(self):
        """Set up test data."""
        self.factory = RequestFactory()

        self.owner = User.objects.create_user(
            username="owner",
            email="owner@example.com"
        )
        self.admin = User.objects.create_user(
            username="admin",
            email="admin@example.com"
        )
        self.member = User.objects.create_user(
            username="member",
            email="member@example.com"
        )
        self.outsider = User.objects.create_user(
            username="outsider",
            email="outsider@example.com"
        )
        self.superuser = User.objects.create_superuser(
            username="superuser",
            email="super@example.com",
            password="pass"
        )

        self.tenant = Tenant.objects.create(name="Test Tenant", slug="test")

        TenantMembership.objects.create(
            user=self.owner,
            tenant=self.tenant,
            role=TenantMembership.Role.OWNER
        )
        TenantMembership.objects.create(
            user=self.admin,
            tenant=self.tenant,
            role=TenantMembership.Role.ADMIN
        )
        TenantMembership.objects.create(
            user=self.member,
            tenant=self.tenant,
            role=TenantMembership.Role.MEMBER
        )

    def test_is_tenant_member_allows_member(self):
        """Test IsTenantMember allows tenant members."""
        request = self.factory.get('/')
        request.user = self.member
        view = APIView()

        permission = IsTenantMember()
        self.assertTrue(permission.has_object_permission(request, view, self.tenant))

    def test_is_tenant_member_allows_admin(self):
        """Test IsTenantMember allows tenant admins."""
        request = self.factory.get('/')
        request.user = self.admin
        view = APIView()

        permission = IsTenantMember()
        self.assertTrue(permission.has_object_permission(request, view, self.tenant))

    def test_is_tenant_member_allows_owner(self):
        """Test IsTenantMember allows tenant owners."""
        request = self.factory.get('/')
        request.user = self.owner
        view = APIView()

        permission = IsTenantMember()
        self.assertTrue(permission.has_object_permission(request, view, self.tenant))

    def test_is_tenant_member_denies_outsider(self):
        """Test IsTenantMember denies non-members."""
        request = self.factory.get('/')
        request.user = self.outsider
        view = APIView()

        permission = IsTenantMember()
        self.assertFalse(permission.has_object_permission(request, view, self.tenant))

    def test_is_tenant_member_allows_superuser(self):
        """Test IsTenantMember allows superuser."""
        request = self.factory.get('/')
        request.user = self.superuser
        view = APIView()

        permission = IsTenantMember()
        self.assertTrue(permission.has_object_permission(request, view, self.tenant))

    def test_is_tenant_owner_allows_owner(self):
        """Test IsTenantOwner allows owner only."""
        request = self.factory.get('/')
        request.user = self.owner
        view = APIView()

        permission = IsTenantOwner()
        self.assertTrue(permission.has_object_permission(request, view, self.tenant))

    def test_is_tenant_owner_denies_admin(self):
        """Test IsTenantOwner denies admin."""
        request = self.factory.get('/')
        request.user = self.admin
        view = APIView()

        permission = IsTenantOwner()
        self.assertFalse(permission.has_object_permission(request, view, self.tenant))

    def test_is_tenant_owner_denies_member(self):
        """Test IsTenantOwner denies regular member."""
        request = self.factory.get('/')
        request.user = self.member
        view = APIView()

        permission = IsTenantOwner()
        self.assertFalse(permission.has_object_permission(request, view, self.tenant))

    def test_is_tenant_owner_allows_superuser(self):
        """Test IsTenantOwner allows superuser."""
        request = self.factory.get('/')
        request.user = self.superuser
        view = APIView()

        permission = IsTenantOwner()
        self.assertTrue(permission.has_object_permission(request, view, self.tenant))

    def test_is_tenant_admin_allows_owner(self):
        """Test IsTenantAdmin allows owner."""
        request = self.factory.get('/')
        request.user = self.owner
        view = APIView()

        permission = IsTenantAdmin()
        self.assertTrue(permission.has_object_permission(request, view, self.tenant))

    def test_is_tenant_admin_allows_admin(self):
        """Test IsTenantAdmin allows admin."""
        request = self.factory.get('/')
        request.user = self.admin
        view = APIView()

        permission = IsTenantAdmin()
        self.assertTrue(permission.has_object_permission(request, view, self.tenant))

    def test_is_tenant_admin_denies_member(self):
        """Test IsTenantAdmin denies regular member."""
        request = self.factory.get('/')
        request.user = self.member
        view = APIView()

        permission = IsTenantAdmin()
        self.assertFalse(permission.has_object_permission(request, view, self.tenant))

    def test_is_tenant_admin_denies_outsider(self):
        """Test IsTenantAdmin denies outsider."""
        request = self.factory.get('/')
        request.user = self.outsider
        view = APIView()

        permission = IsTenantAdmin()
        self.assertFalse(permission.has_object_permission(request, view, self.tenant))

    def test_is_tenant_admin_allows_superuser(self):
        """Test IsTenantAdmin allows superuser."""
        request = self.factory.get('/')
        request.user = self.superuser
        view = APIView()

        permission = IsTenantAdmin()
        self.assertTrue(permission.has_object_permission(request, view, self.tenant))
