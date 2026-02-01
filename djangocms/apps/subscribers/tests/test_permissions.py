"""Tests for subscriber permissions."""
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from rest_framework.views import APIView
from apps.tenants.models import Tenant
from apps.subscribers.models import Subscriber
from apps.subscribers.permissions import IsActiveSubscriber

User = get_user_model()


class SubscriberPermissionsTest(TestCase):
    """Test subscriber permission classes."""

    def setUp(self):
        """Set up test data."""
        self.factory = RequestFactory()
        self.tenant = Tenant.objects.create(name="Test Tenant", slug="test")

        # User with valid subscriber profile
        self.active_user = User.objects.create_user(
            username="active",
            email="active@example.com"
        )
        Subscriber.objects.create(
            user=self.active_user,
            tenant=self.tenant,
            radius_username="active_radius",
            is_active=True
        )

        # User with inactive subscriber profile
        self.inactive_user = User.objects.create_user(
            username="inactive",
            email="inactive@example.com"
        )
        Subscriber.objects.create(
            user=self.inactive_user,
            tenant=self.tenant,
            radius_username="inactive_radius",
            is_active=False
        )

        # User with expired subscriber profile
        self.expired_user = User.objects.create_user(
            username="expired",
            email="expired@example.com"
        )
        past = timezone.now() - timedelta(days=1)
        Subscriber.objects.create(
            user=self.expired_user,
            tenant=self.tenant,
            radius_username="expired_radius",
            is_active=True,
            expires_at=past
        )

        # User without subscriber profile
        self.regular_user = User.objects.create_user(
            username="regular",
            email="regular@example.com"
        )

    def test_is_active_subscriber_allows_valid_subscriber(self):
        """Test IsActiveSubscriber allows user with valid subscription."""
        request = self.factory.get('/')
        request.user = self.active_user
        view = APIView()

        permission = IsActiveSubscriber()
        self.assertTrue(permission.has_permission(request, view))

    def test_is_active_subscriber_denies_inactive_subscriber(self):
        """Test IsActiveSubscriber denies inactive subscriber."""
        request = self.factory.get('/')
        request.user = self.inactive_user
        view = APIView()

        permission = IsActiveSubscriber()
        self.assertFalse(permission.has_permission(request, view))

    def test_is_active_subscriber_denies_expired_subscriber(self):
        """Test IsActiveSubscriber denies expired subscriber."""
        request = self.factory.get('/')
        request.user = self.expired_user
        view = APIView()

        permission = IsActiveSubscriber()
        self.assertFalse(permission.has_permission(request, view))

    def test_is_active_subscriber_denies_non_subscriber(self):
        """Test IsActiveSubscriber denies user without subscriber profile."""
        request = self.factory.get('/')
        request.user = self.regular_user
        view = APIView()

        permission = IsActiveSubscriber()
        self.assertFalse(permission.has_permission(request, view))

    def test_is_active_subscriber_denies_unauthenticated(self):
        """Test IsActiveSubscriber denies unauthenticated user."""
        from django.contrib.auth.models import AnonymousUser

        request = self.factory.get('/')
        request.user = AnonymousUser()
        view = APIView()

        permission = IsActiveSubscriber()
        self.assertFalse(permission.has_permission(request, view))

    def test_is_active_subscriber_with_future_expiry(self):
        """Test IsActiveSubscriber allows subscriber with future expiry."""
        future_user = User.objects.create_user(
            username="future",
            email="future@example.com"
        )
        future = timezone.now() + timedelta(days=30)
        Subscriber.objects.create(
            user=future_user,
            tenant=self.tenant,
            radius_username="future_radius",
            is_active=True,
            expires_at=future
        )

        request = self.factory.get('/')
        request.user = future_user
        view = APIView()

        permission = IsActiveSubscriber()
        self.assertTrue(permission.has_permission(request, view))
