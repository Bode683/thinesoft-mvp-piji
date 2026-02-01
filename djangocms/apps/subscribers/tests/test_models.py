"""Tests for Subscriber model."""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from apps.tenants.models import Tenant
from apps.subscribers.models import Subscriber

User = get_user_model()


class SubscriberModelTest(TestCase):
    """Test Subscriber model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="subscriber",
            email="subscriber@example.com"
        )
        self.tenant = Tenant.objects.create(
            name="Test Tenant",
            slug="test"
        )

    def test_subscriber_creation(self):
        """Test creating a subscriber."""
        subscriber = Subscriber.objects.create(
            user=self.user,
            tenant=self.tenant,
            radius_username="test_radius",
            is_active=True
        )

        self.assertEqual(subscriber.user, self.user)
        self.assertEqual(subscriber.tenant, self.tenant)
        self.assertEqual(subscriber.radius_username, "test_radius")
        self.assertTrue(subscriber.is_active)

    def test_subscriber_str_representation(self):
        """Test subscriber string representation."""
        subscriber = Subscriber.objects.create(
            user=self.user,
            tenant=self.tenant,
            radius_username="test_radius"
        )

        expected = f"test_radius ({self.tenant.slug})"
        self.assertEqual(str(subscriber), expected)

    def test_subscriber_is_valid_when_active_no_expiry(self):
        """Test is_valid returns True for active subscriber without expiry."""
        subscriber = Subscriber.objects.create(
            user=self.user,
            tenant=self.tenant,
            radius_username="test_radius",
            is_active=True,
            expires_at=None
        )

        self.assertTrue(subscriber.is_valid)

    def test_subscriber_is_valid_when_active_future_expiry(self):
        """Test is_valid returns True for active subscriber with future expiry."""
        future = timezone.now() + timedelta(days=30)
        subscriber = Subscriber.objects.create(
            user=self.user,
            tenant=self.tenant,
            radius_username="test_radius",
            is_active=True,
            expires_at=future
        )

        self.assertTrue(subscriber.is_valid)

    def test_subscriber_not_valid_when_inactive(self):
        """Test is_valid returns False for inactive subscriber."""
        subscriber = Subscriber.objects.create(
            user=self.user,
            tenant=self.tenant,
            radius_username="test_radius",
            is_active=False
        )

        self.assertFalse(subscriber.is_valid)

    def test_subscriber_not_valid_when_expired(self):
        """Test is_valid returns False for expired subscriber."""
        past = timezone.now() - timedelta(days=1)
        subscriber = Subscriber.objects.create(
            user=self.user,
            tenant=self.tenant,
            radius_username="test_radius",
            is_active=True,
            expires_at=past
        )

        self.assertFalse(subscriber.is_valid)

    def test_subscriber_data_limit(self):
        """Test subscriber with data limit."""
        subscriber = Subscriber.objects.create(
            user=self.user,
            tenant=self.tenant,
            radius_username="test_radius",
            data_limit_mb=1000
        )

        self.assertEqual(subscriber.data_limit_mb, 1000)

    def test_subscriber_time_limit(self):
        """Test subscriber with time limit."""
        subscriber = Subscriber.objects.create(
            user=self.user,
            tenant=self.tenant,
            radius_username="test_radius",
            time_limit_minutes=60
        )

        self.assertEqual(subscriber.time_limit_minutes, 60)

    def test_radius_username_unique(self):
        """Test radius_username must be unique."""
        Subscriber.objects.create(
            user=self.user,
            tenant=self.tenant,
            radius_username="unique_username"
        )

        user2 = User.objects.create_user(
            username="user2",
            email="user2@example.com"
        )

        with self.assertRaises(Exception):
            Subscriber.objects.create(
                user=user2,
                tenant=self.tenant,
                radius_username="unique_username"
            )

    def test_one_subscriber_per_user(self):
        """Test OneToOneField constraint - one subscriber per user."""
        Subscriber.objects.create(
            user=self.user,
            tenant=self.tenant,
            radius_username="first_username"
        )

        tenant2 = Tenant.objects.create(name="Tenant 2", slug="tenant-2")

        # Should raise error - user already has a subscriber profile
        with self.assertRaises(Exception):
            Subscriber.objects.create(
                user=self.user,
                tenant=tenant2,
                radius_username="second_username"
            )
