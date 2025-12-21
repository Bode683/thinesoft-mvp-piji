# tests.py
from django.test import TestCase, TransactionTestCase
from django.test import override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.conf import settings
from rest_framework.test import APITestCase, APIClient
from rest_framework.authtoken.models import Token
from rest_framework import status
from unittest.mock import patch, Mock, MagicMock
from decimal import Decimal
import json
from datetime import datetime, timedelta
from payments.stripe.providers import StripeProviderV3
from django.utils import timezone

from .models import Payment, PaymentGatewayConfig, PaymentLog
from .serializers import CreatePaymentSerializer, PaymentSerializer
from .tasks import process_webhook, cleanup_old_payments

User = get_user_model()


class PaymentGatewayConfigModelTest(TestCase):
    """Test PaymentGatewayConfig model"""

    def setUp(self):
        self.stripe_config = PaymentGatewayConfig.objects.create(
            name="stripe", variant="stripe", is_active=True, priority=1
        )
        self.paypal_config = PaymentGatewayConfig.objects.create(
            name="paypal", variant="paypal", is_active=True, priority=2
        )

    def test_gateway_config_creation(self):
        """Test gateway configuration creation"""
        self.assertEqual(self.stripe_config.name, "stripe")
        self.assertEqual(self.stripe_config.variant, "stripe")
        self.assertTrue(self.stripe_config.is_active)
        self.assertEqual(self.stripe_config.priority, 1)

    def test_gateway_config_ordering(self):
        """Test gateway configurations are ordered by priority"""
        configs = PaymentGatewayConfig.objects.all()
        self.assertEqual(configs[0], self.paypal_config)  # Higher priority first
        self.assertEqual(configs[1], self.stripe_config)

    def test_gateway_config_str_method(self):
        """Test string representation"""
        expected = "stripe (Active)"
        self.assertEqual(str(self.stripe_config), expected)

        self.stripe_config.is_active = False
        self.stripe_config.save()
        expected = "stripe (Inactive)"
        self.assertEqual(str(self.stripe_config), expected)


class PaymentModelTest(TestCase):
    """Test Payment model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.gateway_config = PaymentGatewayConfig.objects.create(
            name="stripe", variant="stripe", is_active=True, priority=1
        )
        self.payment = Payment.objects.create(
            variant="stripe",
            description="Test payment",
            total=Decimal("29.99"),
            currency="USD",
            user=self.user,
            order_id="ORDER-123",
            payment_gateway=self.gateway_config,
            metadata={"product_id": 456},
        )

    def test_payment_creation(self):
        """Test payment creation"""
        self.assertEqual(self.payment.variant, "stripe")
        self.assertEqual(self.payment.total, Decimal("29.99"))
        self.assertEqual(self.payment.currency, "USD")
        self.assertEqual(self.payment.user, self.user)
        self.assertEqual(self.payment.order_id, "ORDER-123")
        self.assertEqual(self.payment.payment_gateway, self.gateway_config)
        self.assertEqual(self.payment.metadata["product_id"], 456)

    def test_payment_urls(self):
        """Test payment URL generation"""
        success_url = self.payment.get_success_url()
        failure_url = self.payment.get_failure_url()

        self.assertIn(str(self.payment.id), success_url)
        self.assertIn("success", success_url)
        self.assertIn(str(self.payment.id), failure_url)
        self.assertIn("failure", failure_url)

    def test_payment_host(self):
        """Test payment host retrieval"""
        host = self.payment.get_host()
        self.assertEqual(host, settings.PAYMENT_HOST)


class PaymentLogModelTest(TestCase):
    """Test PaymentLog model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.gateway_config = PaymentGatewayConfig.objects.create(
            name="stripe", variant="stripe", is_active=True, priority=1
        )
        self.payment = Payment.objects.create(
            variant="stripe",
            description="Test payment",
            total=Decimal("29.99"),
            currency="USD",
            user=self.user,
            payment_gateway=self.gateway_config,
        )

    def test_payment_log_creation(self):
        """Test payment log creation"""
        log = PaymentLog.objects.create(
            payment=self.payment,
            event_type="PAYMENT_CREATED",
            message="Payment created successfully",
            data={"amount": "29.99", "currency": "USD"},
        )

        self.assertEqual(log.payment, self.payment)
        self.assertEqual(log.event_type, "PAYMENT_CREATED")
        self.assertEqual(log.message, "Payment created successfully")
        self.assertEqual(log.data["amount"], "29.99")

    def test_payment_log_ordering(self):
        """Test payment logs are ordered by creation time (newest first)"""
        log1 = PaymentLog.objects.create(
            payment=self.payment, event_type="PAYMENT_CREATED", message="First log"
        )
        log2 = PaymentLog.objects.create(
            payment=self.payment, event_type="PAYMENT_CONFIRMED", message="Second log"
        )

        logs = PaymentLog.objects.all()
        self.assertEqual(logs[0], log2)  # Newest first
        self.assertEqual(logs[1], log1)


class PaymentSerializerTest(TestCase):
    """Test payment serializers"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        PaymentGatewayConfig.objects.create(
            name="stripe", variant="stripe", is_active=True, priority=1
        )

    def test_create_payment_serializer_valid_data(self):
        """Test CreatePaymentSerializer with valid data"""
        data = {
            "amount": "29.99",
            "currency": "USD",
            "description": "Test payment",
            "gateway": "stripe",
            "order_id": "ORDER-123",
            "metadata": {"product_id": 456},
        }
        serializer = CreatePaymentSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["amount"], Decimal("29.99"))

    def test_create_payment_serializer_invalid_gateway(self):
        """Test CreatePaymentSerializer with invalid gateway"""
        data = {
            "amount": "29.99",
            "currency": "USD",
            "description": "Test payment",
            "gateway": "invalid_gateway",
        }
        serializer = CreatePaymentSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("gateway", serializer.errors)

    def test_create_payment_serializer_invalid_amount(self):
        """Test CreatePaymentSerializer with invalid amount"""
        data = {
            "amount": "0.00",
            "currency": "USD",
            "description": "Test payment",
            "gateway": "stripe",
        }
        serializer = CreatePaymentSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("amount", serializer.errors)

    def test_payment_serializer(self):
        """Test PaymentSerializer"""
        gateway_config = PaymentGatewayConfig.objects.get(name="stripe")
        payment = Payment.objects.create(
            variant="stripe",
            description="Test payment",
            total=Decimal("29.99"),
            currency="USD",
            user=self.user,
            payment_gateway=gateway_config,
        )

        serializer = PaymentSerializer(payment)
        data = serializer.data

        self.assertEqual(data["total"], "29.99")
        self.assertEqual(data["currency"], "USD")
        self.assertEqual(data["gateway_name"], "stripe")


class PaymentGatewayAPITest(APITestCase):
    """Test PaymentGateway API endpoints"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.token = Token.objects.create(user=self.user)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

        self.stripe_config = PaymentGatewayConfig.objects.create(
            name="stripe", variant="stripe", is_active=True, priority=1
        )
        self.paypal_config = PaymentGatewayConfig.objects.create(
            name="paypal", variant="paypal", is_active=True, priority=2
        )
        self.inactive_config = PaymentGatewayConfig.objects.create(
            name="inactive", variant="inactive", is_active=False, priority=0
        )

    def test_list_active_gateways(self):
        """Test listing only active gateways"""
        url = reverse("gateway-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Only active gateways
        gateway_names = [g["name"] for g in response.data]
        self.assertIn("stripe", gateway_names)
        self.assertIn("paypal", gateway_names)
        self.assertNotIn("inactive", gateway_names)

    def test_list_gateways_unauthenticated(self):
        """Test accessing gateways without authentication"""
        self.client.credentials()  # Remove authentication
        url = reverse("gateway-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PaymentAPITest(APITestCase):
    """Test Payment API endpoints"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.other_user = User.objects.create_user(
            username="otheruser", email="other@example.com", password="testpass123"
        )
        self.token = Token.objects.create(user=self.user)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

        self.gateway_config = PaymentGatewayConfig.objects.create(
            name="stripe", variant="stripe", is_active=True, priority=1
        )

        self.payment = Payment.objects.create(
            variant="stripe",
            description="Test payment",
            total=Decimal("29.99"),
            currency="USD",
            user=self.user,
            payment_gateway=self.gateway_config,
        )

        # Payment for other user (should not be accessible)
        self.other_payment = Payment.objects.create(
            variant="stripe",
            description="Other user payment",
            total=Decimal("19.99"),
            currency="USD",
            user=self.other_user,
            payment_gateway=self.gateway_config,
        )

    def test_list_user_payments(self):
        """Test listing payments for authenticated user only"""
        url = reverse("payment-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.payment.id)

    @override_settings(USE_LOCALSTRIPE=False)
    def test_create_payment_success_checkout(self):
        """Test successful payment creation for Checkout flow (non-local)."""
        # Patch Payment.get_form to raise RedirectNeeded with a URL
        from payments import RedirectNeeded

        url = reverse("payment-create-payment")
        data = {
            "amount": "49.99",
            "currency": "USD",
            "description": "New test payment",
            "gateway": "stripe",
            "order_id": "ORDER-456",
            "metadata": {"product_id": 789},
        }
        with patch(
            "payment_gateway.views.Payment.get_form",
            side_effect=RedirectNeeded("https://checkout.stripe.com/pay/test"),
        ):
            response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("payment_id", response.data)
        self.assertIn("gateway_url", response.data)
        self.assertEqual(response.data["amount"], Decimal("49.99"))
        self.assertEqual(response.data["currency"], "USD")

        payment = Payment.objects.get(id=response.data["payment_id"])
        self.assertEqual(payment.user, self.user)
        self.assertEqual(payment.total, Decimal("49.99"))
        self.assertEqual(payment.order_id, "ORDER-456")
        self.assertEqual(payment.metadata["product_id"], 789)

        self.assertTrue(payment.logs.filter(event_type="PAYMENT_CREATED").exists())

    @override_settings(USE_LOCALSTRIPE=True)
    @patch("stripe.PaymentIntent.create")
    def test_create_payment_success_local_intent(self, mock_pi_create):
        """Test successful payment creation for local PaymentIntent flow."""
        mock_pi_create.return_value = {
            "id": "pi_test_123",
            "status": "succeeded",
            "client_secret": "cs_test_123",
        }

        url = reverse("payment-create-payment")
        data = {
            "amount": "49.99",
            "currency": "USD",
            "description": "New test payment local",
            "gateway": "stripe",
            "order_id": "ORDER-457",
            "metadata": {"product_id": 790},
        }
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("payment_id", response.data)
        self.assertIn("intent_id", response.data)
        self.assertIn("client_secret", response.data)
        self.assertEqual(response.data["amount"], Decimal("49.99"))
        self.assertEqual(response.data["currency"], "USD")

        payment = Payment.objects.get(id=response.data["payment_id"])
        self.assertEqual(payment.user, self.user)
        self.assertEqual(payment.total, Decimal("49.99"))
        self.assertEqual(payment.order_id, "ORDER-457")
        self.assertEqual(payment.metadata["product_id"], 790)
        self.assertEqual(payment.transaction_id, "pi_test_123")
        # status should be confirmed when PI is succeeded
        self.assertEqual(payment.status, "confirmed")
        self.assertTrue(payment.logs.filter(event_type="PI_CREATED").exists())

    def test_create_payment_invalid_gateway(self):
        """Test payment creation with invalid gateway"""
        url = reverse("payment-create-payment")
        data = {
            "amount": "49.99",
            "currency": "USD",
            "description": "New test payment",
            "gateway": "invalid_gateway",
        }
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("gateway", response.data)

    def test_create_payment_inactive_gateway(self):
        """Test payment creation with inactive gateway"""
        inactive_gateway = PaymentGatewayConfig.objects.create(
            name="inactive", variant="inactive", is_active=False, priority=0
        )

        url = reverse("payment-create-payment")
        data = {
            "amount": "49.99",
            "currency": "USD",
            "description": "New test payment",
            "gateway": "inactive",
        }
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("payment_gateway.models.Payment.capture")
    def test_capture_payment_success(self):
        """Test successful payment capture"""
        # Set payment to preauth status
        self.payment.status = "preauth"
        self.payment.save()

        url = reverse("payment-capture", kwargs={"pk": self.payment.id})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_capture.assert_called_once()

        # Verify log was created
        self.assertTrue(
            PaymentLog.objects.filter(
                payment=self.payment, event_type="PAYMENT_CAPTURED"
            ).exists()
        )

    def test_capture_payment_wrong_status(self):
        """Test capturing payment with wrong status"""
        # Payment is in 'waiting' status by default
        url = reverse("payment-capture", kwargs={"pk": self.payment.id})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("not in preauth status", response.data["error"])

    @patch("payment_gateway.models.Payment.refund")
    def test_refund_payment_success(self):
        """Test successful payment refund"""
        # Set payment to confirmed status
        self.payment.status = "confirmed"
        self.payment.save()

        url = reverse("payment-refund", kwargs={"pk": self.payment.id})
        response = self.client.post(url, {"amount": "10.00"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_refund.assert_called_once_with(amount=Decimal("10.00"))

        # Verify log was created
        self.assertTrue(
            PaymentLog.objects.filter(
                payment=self.payment, event_type="PAYMENT_REFUNDED"
            ).exists()
        )

    @patch("payment_gateway.models.Payment.refund")
    def test_refund_payment_full_amount(self):
        """Test full payment refund"""
        self.payment.status = "confirmed"
        self.payment.save()

        url = reverse("payment-refund", kwargs={"pk": self.payment.id})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_refund.assert_called_once_with()  # No amount specified = full refund

    def test_refund_payment_wrong_status(self):
        """Test refunding payment with wrong status"""
        url = reverse("payment-refund", kwargs={"pk": self.payment.id})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("not confirmed", response.data["error"])

    def test_payment_logs(self):
        """Test retrieving payment logs"""
        # Create some logs
        PaymentLog.objects.create(
            payment=self.payment,
            event_type="PAYMENT_CREATED",
            message="Payment created",
        )
        PaymentLog.objects.create(
            payment=self.payment,
            event_type="PAYMENT_CONFIRMED",
            message="Payment confirmed",
        )

        url = reverse("payment-logs", kwargs={"pk": self.payment.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_access_other_user_payment(self):
        """Test accessing payment of another user"""
        url = reverse("payment-detail", kwargs={"pk": self.other_payment.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class WebhookTest(TestCase):
    """Test webhook functionality"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.gateway_config = PaymentGatewayConfig.objects.create(
            name="stripe", variant="stripe", is_active=True, priority=1
        )
        self.payment = Payment.objects.create(
            variant="stripe",
            description="Test payment",
            total=Decimal("29.99"),
            currency="USD",
            user=self.user,
            payment_gateway=self.gateway_config,
        )

    @override_settings(USE_LOCALSTRIPE=False)
    @patch("payment_gateway.webhooks.import_string")
    def test_stripe_webhook_success(self, mock_import_string):
        """Test successful Stripe webhook processing using verified signature (secure_endpoint=True)"""

        # Fake provider with return_event_payload and process_data
        class FakeProvider:
            def __init__(self, **kwargs):
                pass

            def return_event_payload(self, request):
                return {
                    "type": "checkout.session.completed",
                    "data": {
                        "object": {"client_reference_id": str(self.payment.token)}
                    },
                }

            def process_data(self, payment, request):
                from payments import PaymentStatus

                payment.change_status(PaymentStatus.CONFIRMED)
                payment.save()
                from django.http import HttpResponse

                return HttpResponse(status=200)

        mock_import_string.return_value = FakeProvider

        url = reverse("webhook", kwargs={"variant": "stripe"})
        response = self.client.post(
            url,
            data=json.dumps({"ignored": True}),
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="test_signature",
        )

        self.assertEqual(response.status_code, 200)
        # Payment should be confirmed by provider logic
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, "confirmed")

    @override_settings(USE_LOCALSTRIPE=True)
    def test_localstripe_payment_intent_webhook_succeeded(self):
        """Localstripe PaymentIntent succeeded updates payment status to confirmed."""
        # create payment and set token in metadata in PI event
        url = reverse("webhook", kwargs={"variant": "stripe"})
        payload = {
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "id": "pi_local_1",
                    "status": "succeeded",
                    "metadata": {"payment_id": str(self.payment.id)},
                }
            },
        }
        resp = self.client.post(
            url, data=json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(resp.status_code, 200)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, "confirmed")

    @override_settings(USE_LOCALSTRIPE=True)
    def test_localstripe_payment_intent_missing_payment_id(self):
        """Localstripe PaymentIntent webhook without payment_id should 400."""
        url = reverse("webhook", kwargs={"variant": "stripe"})
        payload = {
            "type": "payment_intent.succeeded",
            "data": {"object": {"id": "pi_2"}},
        }
        resp = self.client.post(
            url, data=json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(resp.status_code, 400)

    @override_settings(USE_LOCALSTRIPE=True)
    def test_localstripe_non_payment_intent_event_acknowledged(self):
        """Non payment_intent.* events should be acknowledged with 200 in localstripe mode."""
        url = reverse("webhook", kwargs={"variant": "stripe"})
        payload = {"type": "product.created", "data": {"object": {"id": "prod_1"}}}
        resp = self.client.post(
            url, data=json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(resp.status_code, 200)

    @override_settings(USE_LOCALSTRIPE=False)
    @patch("payment_gateway.webhooks.import_string")
    def test_stripe_webhook_invalid_signature(self, mock_import_string):
        """Test Stripe webhook with invalid signature"""
        import stripe

        class FakeProvider:
            def __init__(self, **kwargs):
                pass

            def return_event_payload(self, request):
                raise stripe.error.SignatureVerificationError(
                    "Invalid signature", "sig_header"
                )

        mock_import_string.return_value = FakeProvider

        url = reverse("webhook", kwargs={"variant": "stripe"})
        response = self.client.post(
            url,
            data=json.dumps({"test": "data"}),
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="invalid_signature",
        )

        self.assertEqual(response.status_code, 400)

    @patch("payment_gateway.webhooks.import_string")
    def test_stripe_webhook_local_unsecured(self):
        """Test Stripe webhook in local mode without signature verification (secure_endpoint=False)"""

        # Use fake provider to bypass Stripe internals
        class FakeProvider:
            def __init__(self, **kwargs):
                pass

            def return_event_payload(self, request):
                return {
                    "type": "checkout.session.completed",
                    "data": {
                        "object": {"client_reference_id": str(self.payment.token)}
                    },
                }

            def process_data(self, payment, request):
                from payments import PaymentStatus

                payment.change_status(PaymentStatus.CONFIRMED)
                payment.save()
                from django.http import HttpResponse

                return HttpResponse(status=200)

        mock_import_string.return_value = FakeProvider

        url = reverse("webhook", kwargs={"variant": "stripe"})
        response = self.client.post(
            url,
            data=json.dumps({"dummy": True}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, "confirmed")

    def test_paypal_webhook_success(self):
        """Test successful PayPal webhook processing"""
        url = reverse("webhook", kwargs={"variant": "paypal"})
        response = self.client.post(
            url,
            data=json.dumps(
                {
                    "event_type": "PAYMENT.CAPTURE.COMPLETED",
                    "resource": {"id": "PAYPAL123"},
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)

    def test_unknown_webhook_variant(self):
        """Test webhook with unknown variant"""
        url = reverse("webhook", kwargs={"variant": "unknown"})
        response = self.client.post(
            url, data=json.dumps({"test": "data"}), content_type="application/json"
        )

        self.assertEqual(response.status_code, 400)


class TaskTest(TransactionTestCase):
    """Test Celery tasks"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.gateway_config = PaymentGatewayConfig.objects.create(
            name="stripe", variant="stripe", is_active=True, priority=1
        )
        self.payment = Payment.objects.create(
            variant="stripe",
            description="Test payment",
            total=Decimal("29.99"),
            currency="USD",
            user=self.user,
            payment_gateway=self.gateway_config,
        )

    def test_process_webhook_task(self):
        """Test webhook processing task"""
        event_data = {"event_type": "payment_succeeded", "payment_id": "test123"}

        result = process_webhook.apply(args=[str(self.payment.id), event_data]).get()

        # Refresh payment from database
        self.payment.refresh_from_db()

        self.assertTrue(self.payment.webhook_received)
        self.assertIn("processed", result)

        # Verify log was created
        self.assertTrue(
            PaymentLog.objects.filter(
                payment=self.payment, event_type="WEBHOOK_RECEIVED"
            ).exists()
        )

    def test_process_webhook_task_payment_not_found(self):
        """Test webhook processing task with non-existent payment"""
        event_data = {"event_type": "payment_succeeded"}

        result = process_webhook.apply(args=["99999", event_data]).get()

        self.assertIn("not found", result)

    def test_cleanup_old_payments_task(self):
        """Test cleanup old payments task"""
        # Create old payment
        old_payment = Payment.objects.create(
            variant="stripe",
            description="Old payment",
            total=Decimal("19.99"),
            currency="USD",
            user=self.user,
            payment_gateway=self.gateway_config,
            status="waiting",
        )

        # Make it old by manually setting created date
        old_date = timezone.now() - timedelta(days=8)
        Payment.objects.filter(id=old_payment.id).update(created=old_date)

        result = cleanup_old_payments.apply().get()

        # Refresh from database
        old_payment.refresh_from_db()

        self.assertEqual(old_payment.status, "error")
        self.assertIn("Cleaned up 1", result)


class StripeProviderFlowTest(TestCase):
    """Tests for StripeProviderV3 core flows"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="provuser", email="prov@example.com", password="testpass123"
        )
        self.gateway_config = PaymentGatewayConfig.objects.create(
            name="stripe", variant="stripe", is_active=True, priority=1
        )
        self.payment = Payment.objects.create(
            variant="stripe",
            description="Flow payment",
            total=Decimal("12.34"),
            currency="USD",
            user=self.user,
            payment_gateway=self.gateway_config,
        )

    @patch("payments.stripe.providers.stripe.checkout.Session.create")
    def test_session_creation_success(self):
        from payments import RedirectNeeded

        provider = StripeProviderV3(
            api_key="sk_test_123", endpoint_secret="whsec_123", secure_endpoint=False
        )

        mock_create.return_value = {"id": "cs_test_ok", "url": "https://stripe/ok"}

        with self.assertRaises(RedirectNeeded):
            provider.get_form(self.payment)

        self.payment.refresh_from_db()
        self.assertEqual(self.payment.transaction_id, "cs_test_ok")
        # attrs is a PaymentAttributeProxy; use attribute access
        self.assertIsNotNone(getattr(self.payment.attrs, "session", None))
        self.assertEqual(self.payment.attrs.session["url"], "https://stripe/ok")

    @patch("payments.stripe.providers.stripe.checkout.Session.create")
    def test_session_creation_failure(self):
        from payments import PaymentError
        import stripe

        provider = StripeProviderV3(
            api_key="sk_test_123", endpoint_secret="whsec_123", secure_endpoint=False
        )

        mock_create.side_effect = stripe.error.StripeError("boom")

        with self.assertRaises(PaymentError):
            provider.get_form(self.payment)

        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, "error")

    @patch("payments.stripe.providers.stripe.checkout.Session.retrieve")
    def test_status_polling_paid(self):
        from payments import PaymentStatus

        provider = StripeProviderV3(
            api_key="sk_test_123", endpoint_secret="whsec_123", secure_endpoint=False
        )
        # Simulate existing session id
        self.payment.transaction_id = "cs_status_1"
        self.payment.save()

        # Return JSON-serializable dict with attribute access
        class AttrDict(dict):
            __getattr__ = dict.get

        mock_retrieve.return_value = AttrDict(payment_status="paid")

        provider.status(self.payment)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, PaymentStatus.CONFIRMED)

    @patch("payments.stripe.providers.stripe.checkout.Session.retrieve")
    def test_status_polling_unpaid(self):
        from payments import PaymentStatus

        provider = StripeProviderV3(
            api_key="sk_test_123", endpoint_secret="whsec_123", secure_endpoint=False
        )
        self.payment.transaction_id = "cs_status_2"
        self.payment.save()

        class AttrDict(dict):
            __getattr__ = dict.get

        mock_retrieve.return_value = AttrDict(payment_status="unpaid")

        provider.status(self.payment)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, PaymentStatus.WAITING)

    @patch("payments.stripe.providers.stripe.Refund.create")
    def test_refund_success(self):
        from payments import PaymentStatus

        provider = StripeProviderV3(
            api_key="sk_test_123", endpoint_secret="whsec_123", secure_endpoint=False
        )
        # Prepare confirmed payment with session/payment_intent
        self.payment.status = PaymentStatus.CONFIRMED
        # PaymentAttributeProxy requires attribute assignment, not item assignment
        self.payment.attrs.session = {"payment_intent": "pi_123"}
        self.payment.save()

        mock_refund.return_value = {"id": "re_123"}

        refunded_cents = provider.refund(self.payment)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, PaymentStatus.REFUNDED)
        self.assertTrue(refunded_cents > 0)
        self.assertIsNotNone(getattr(self.payment.attrs, "refund", None))

    @patch("payments.stripe.providers.stripe.Refund.create")
    def test_refund_failure(self):
        from payments import PaymentError, PaymentStatus
        import stripe

        provider = StripeProviderV3(
            api_key="sk_test_123", endpoint_secret="whsec_123", secure_endpoint=False
        )
        self.payment.status = PaymentStatus.CONFIRMED
        self.payment.attrs.session = {"payment_intent": "pi_123"}
        self.payment.save()

        mock_refund.side_effect = stripe.error.StripeError("nope")

        with self.assertRaises(PaymentError):
            provider.refund(self.payment)

    @override_settings(
        PAYMENT_VARIANTS={
            "stripe": (
                "payments.stripe.providers.StripeProviderV3",
                {
                    "api_key": "sk_test_123",
                    "endpoint_secret": "whsec_123",
                    "secure_endpoint": True,
                },
            )
        }
    )
    def test_secure_endpoint_missing_signature_header(self):
        """When secure_endpoint=True and no signature header, webhook should 400"""
        url = reverse("webhook", kwargs={"variant": "stripe"})
        response = self.client.post(
            url,
            data=json.dumps(
                {"type": "checkout.session.completed", "data": {"object": {}}}
            ),
            content_type="application/json",
            # No HTTP_STRIPE_SIGNATURE header on purpose
        )
        self.assertEqual(response.status_code, 400)

    def test_zero_decimal_conversion(self):
        provider = StripeProviderV3(
            api_key="sk_test_123", endpoint_secret="whsec_123", secure_endpoint=False
        )
        # JPY should not multiply by 100
        self.assertEqual(provider.convert_amount("JPY", Decimal("1000")), 1000)
        # USD should multiply by 100
        self.assertEqual(provider.convert_amount("USD", Decimal("12.34")), 1234)


class IntegrationTest(APITestCase):
    """Integration tests for complete payment flow"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.token = Token.objects.create(user=self.user)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

        self.gateway_config = PaymentGatewayConfig.objects.create(
            name="stripe", variant="stripe", is_active=True, priority=1
        )

    @patch("payment_gateway.views.Payment.get_form")
    @patch("payment_gateway.models.Payment.capture")
    def test_complete_payment_flow(self, mock_capture, mock_get_form):
        """Test complete payment flow from creation to capture"""
        from payments import RedirectNeeded

        mock_get_form.side_effect = RedirectNeeded(
            "https://checkout.stripe.com/pay/test"
        )

        # 1. Create payment
        create_url = reverse("payment-create-payment")
        create_data = {
            "amount": "99.99",
            "currency": "USD",
            "description": "Integration test payment",
            "gateway": "stripe",
            "order_id": "ORDER-INTEGRATION-123",
        }
        create_response = self.client.post(create_url, create_data, format="json")

        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        payment_id = create_response.data["payment_id"]

        # 2. Verify payment was created
        payment = Payment.objects.get(id=payment_id)
        self.assertEqual(payment.total, Decimal("99.99"))
        self.assertEqual(payment.status, "waiting")

        # 3. Simulate payment confirmation (would normally come from webhook)
        payment.status = "preauth"
        payment.save()

        # 4. Capture payment
        capture_url = reverse("payment-capture", kwargs={"pk": payment_id})
        capture_response = self.client.post(capture_url)

        self.assertEqual(capture_response.status_code, status.HTTP_200_OK)
        mock_capture.assert_called_once()

        # 5. Check logs
        logs_url = reverse("payment-logs", kwargs={"pk": payment_id})
        logs_response = self.client.get(logs_url)

        self.assertEqual(logs_response.status_code, status.HTTP_200_OK)
        log_events = [log["event_type"] for log in logs_response.data]
        self.assertIn("PAYMENT_CREATED", log_events)
        self.assertIn("PAYMENT_CAPTURED", log_events)

    def test_success_and_failure_redirect_endpoints(self):
        """Ensure success/failure endpoints log and return 200."""
        # Create a payment for current user
        pay = Payment.objects.create(
            variant="stripe",
            description="Redirect test",
            total=Decimal("10.00"),
            currency="USD",
            user=self.user,
            payment_gateway=self.gateway_config,
        )

        success_url = reverse("payment-success", kwargs={"pk": pay.id})
        failure_url = reverse("payment-failure", kwargs={"pk": pay.id})

        r1 = self.client.get(success_url)
        self.assertEqual(r1.status_code, status.HTTP_200_OK)
        r2 = self.client.get(failure_url)
        self.assertEqual(r2.status_code, status.HTTP_200_OK)

        self.assertTrue(pay.logs.filter(event_type="PAYMENT_SUCCESS_REDIRECT").exists())
        self.assertTrue(pay.logs.filter(event_type="PAYMENT_FAILURE_REDIRECT").exists())


class SubscriptionAPITest(APITestCase):
    """Tests for subscription endpoints in SubscriptionViewSet."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="subuser", email="sub@example.com", password="testpass123"
        )
        self.token = Token.objects.create(user=self.user)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

        self.gateway_config = PaymentGatewayConfig.objects.create(
            name="stripe", variant="stripe", is_active=True, priority=1
        )

        # Create Plan and Pricing
        from payment_gateway.models import Plan, PlanPricing

        self.plan = Plan.objects.create(
            name="Premium",
            description="Monthly premium",
            available=True,
            auto_renew=True,
        )
        self.pricing = PlanPricing.objects.create(
            plan=self.plan,
            amount=Decimal("200.00"),
            currency="USD",
            interval="month",
            active=True,
            stripe_price_id="price_123",  # used as plan id in localstripe too
        )

    def test_list_plans(self):
        url = reverse("subscription-plans")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(resp.data), 1)

    @override_settings(USE_LOCALSTRIPE=True)
    @patch("stripe.Customer.create")
    @patch("stripe.Customer.list")
    @patch("stripe.PaymentMethod.attach")
    @patch("stripe.Customer.modify")
    @patch("stripe.Subscription.create")
    def test_subscribe_local(
        self,
        mock_sub_create,
        mock_cust_modify,
        mock_pm_attach,
        mock_cust_list,
        mock_cust_create,
    ):
        mock_cust_list.return_value = Mock(data=[])
        mock_cust_create.return_value = {"id": "cus_123"}
        mock_sub_create.return_value = {
            "id": "sub_123",
            "status": "active",
            "current_period_end": 1234567890,
        }

        url = reverse("subscription-subscribe")
        resp = self.client.post(url, {"plan_id": self.plan.id}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["subscription_id"], "sub_123")

    @patch("stripe.Subscription.modify")
    def test_cancel_subscription(self, mock_modify):
        mock_modify.return_value = {"id": "sub_123", "status": "active"}
        url = reverse("subscription-cancel")
        resp = self.client.post(url, {"subscription_id": "sub_123"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["subscription_id"], "sub_123")

    @override_settings(USE_LOCALSTRIPE=True)
    @patch("stripe.Customer.create")
    @patch("stripe.Customer.list")
    @patch("stripe.Subscription.list")
    def test_status_lists_subscriptions(
        self, mock_sub_list, mock_cust_list, mock_cust_create
    ):
        mock_cust_list.return_value = Mock(data=[])
        mock_cust_create.return_value = {"id": "cus_123"}
        # Localstripe uses legacy plan on items
        mock_sub_list.return_value = {
            "data": [
                {
                    "id": "sub_123",
                    "status": "active",
                    "current_period_end": 123,
                    "items": {"data": [{"plan": {"id": self.pricing.stripe_price_id}}]},
                }
            ]
        }
        url = reverse("subscription-status")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]["subscription_id"], "sub_123")

    @override_settings(USE_LOCALSTRIPE=True)
    @patch("stripe.Customer.create")
    @patch("stripe.Customer.list")
    @patch("stripe.Subscription.list")
    def test_me_limits_uses_active_subscription_or_default(
        self, mock_sub_list, mock_cust_list, mock_cust_create
    ):
        mock_cust_list.return_value = Mock(data=[])
        mock_cust_create.return_value = {"id": "cus_123"}
        mock_sub_list.return_value = {
            "data": [
                {
                    "id": "sub_123",
                    "status": "active",
                    "current_period_end": 123,
                    "items": {"data": [{"plan": {"id": self.pricing.stripe_price_id}}]},
                }
            ]
        }
        url = reverse("subscription-me-limits")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["plan_id"], self.plan.id)

    @patch("payment_gateway.models.Payment.get_payment_url")
    @patch("payment_gateway.models.Payment.refund")
    def test_payment_refund_flow(self, mock_refund, mock_get_payment_url):
        """Test payment refund flow"""
        mock_get_payment_url.return_value = "https://checkout.stripe.com/pay/test"

        # Create and confirm payment
        payment = Payment.objects.create(
            variant="stripe",
            description="Refund test payment",
            total=Decimal("50.00"),
            currency="USD",
            user=self.user,
            payment_gateway=self.gateway_config,
            status="confirmed",
        )

        # Refund partial amount
        refund_url = reverse("payment-refund", kwargs={"pk": payment.id})
        refund_response = self.client.post(refund_url, {"amount": "25.00"})

        self.assertEqual(refund_response.status_code, status.HTTP_200_OK)
        mock_refund.assert_called_once_with(amount=Decimal("25.00"))

        # Verify refund log
        refund_log = PaymentLog.objects.filter(
            payment=payment, event_type="PAYMENT_REFUNDED"
        ).first()
        self.assertIsNotNone(refund_log)
        self.assertIn("25.00", refund_log.message)


class AdminTest(TestCase):
    """Test admin interface"""

    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="adminpass123"
        )
        self.client.force_login(self.admin_user)

        self.gateway_config = PaymentGatewayConfig.objects.create(
            name="stripe", variant="stripe", is_active=True, priority=1
        )

    def test_payment_gateway_config_admin(self):
        """Test PaymentGatewayConfig admin interface"""
        url = "/admin/payment_gateway/paymentgatewayconfig/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_payment_admin(self):
        """Test Payment admin interface"""
        url = "/admin/payment_gateway/payment/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_payment_log_admin(self):
        """Test PaymentLog admin interface"""
        url = "/admin/payment_gateway/paymentlog/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)


class SecurityTest(APITestCase):
    """Test security aspects of the payment gateway"""

    def setUp(self):
        self.user1 = User.objects.create_user(
            username="user1", email="user1@example.com", password="testpass123"
        )
        self.user2 = User.objects.create_user(
            username="user2", email="user2@example.com", password="testpass123"
        )

        self.token1 = Token.objects.create(user=self.user1)
        self.token2 = Token.objects.create(user=self.user2)

        self.gateway_config = PaymentGatewayConfig.objects.create(
            name="stripe", variant="stripe", is_active=True, priority=1
        )

        self.payment1 = Payment.objects.create(
            variant="stripe",
            description="User1 payment",
            total=Decimal("29.99"),
            currency="USD",
            user=self.user1,
            payment_gateway=self.gateway_config,
        )

        self.payment2 = Payment.objects.create(
            variant="stripe",
            description="User2 payment",
            total=Decimal("39.99"),
            currency="USD",
            user=self.user2,
            payment_gateway=self.gateway_config,
        )

    def test_user_cannot_access_other_users_payments(self):
        """Test that users can only access their own payments"""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")

        # Try to access user2's payment
        url = reverse("payment-detail", kwargs={"pk": self.payment2.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Can access own payment
        url = reverse("payment-detail", kwargs={"pk": self.payment1.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_cannot_modify_other_users_payments(self):
        """Test that users cannot modify other users' payments"""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")

        # Set payment2 to preauth status
        self.payment2.status = "preauth"
        self.payment2.save()

        # Try to capture user2's payment
        url = reverse("payment-capture", kwargs={"pk": self.payment2.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthenticated_access_denied(self):
        """Test that unauthenticated requests are denied"""
        # No authentication token
        self.client.credentials()

        url = reverse("payment-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        url = reverse("payment-create-payment")
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invalid_token_access_denied(self):
        """Test that invalid tokens are rejected"""
        self.client.credentials(HTTP_AUTHORIZATION="Token invalid_token_123")

        url = reverse("payment-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_payment_amount_validation(self):
        """Test that payment amounts are properly validated"""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")

        url = reverse("payment-create-payment")

        # Test negative amount
        data = {
            "amount": "-10.00",
            "currency": "USD",
            "description": "Test payment",
            "gateway": "stripe",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Test zero amount
        data["amount"] = "0.00"
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Test very large amount (should be allowed but flagged)
        data["amount"] = "999999.99"
        response = self.client.post(url, data, format="json")
        # This should succeed but might trigger additional validation in real implementation
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_sql_injection_protection(self):
        """Test protection against SQL injection"""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")

        url = reverse("payment-create-payment")
        data = {
            "amount": "29.99",
            "currency": "USD",
            "description": "'; DROP TABLE payments; --",
            "gateway": "stripe",
            "order_id": "' OR 1=1 --",
        }
        response = self.client.post(url, data, format="json")

        # Should create payment normally (Django ORM protects against SQL injection)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify the malicious strings were stored as regular data
        payment = Payment.objects.get(id=response.data["payment_id"])
        self.assertEqual(payment.description, "'; DROP TABLE payments; --")
        self.assertEqual(payment.order_id, "' OR 1=1 --")

    def test_xss_protection(self):
        """Test protection against XSS attacks"""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")

        url = reverse("payment-create-payment")
        xss_payload = '<script>alert("xss")</script>'
        data = {
            "amount": "29.99",
            "currency": "USD",
            "description": xss_payload,
            "gateway": "stripe",
        }
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify the script tag was stored as regular text
        payment = Payment.objects.get(id=response.data["payment_id"])
        self.assertEqual(payment.description, xss_payload)


class PerformanceTest(APITestCase):
    """Test performance aspects of the payment gateway"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.token = Token.objects.create(user=self.user)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

        self.gateway_config = PaymentGatewayConfig.objects.create(
            name="stripe", variant="stripe", is_active=True, priority=1
        )

    def test_bulk_payment_creation(self):
        """Test creating multiple payments efficiently"""
        import time

        start_time = time.time()

        # Create 10 payments
        for i in range(10):
            url = reverse("payment-create-payment")
            data = {
                "amount": f"{10.00 + i}.99",
                "currency": "USD",
                "description": f"Bulk test payment {i}",
                "gateway": "stripe",
                "order_id": f"BULK-{i}",
            }
            with patch("payment_gateway.views.Payment.get_form") as mock_url:
                from payments import RedirectNeeded

                mock_url.side_effect = RedirectNeeded(
                    "https://checkout.stripe.com/pay/test"
                )
                response = self.client.post(url, data, format="json")
                self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        end_time = time.time()
        execution_time = end_time - start_time

        # Should complete within reasonable time (adjust threshold as needed)
        self.assertLess(execution_time, 10.0, "Bulk payment creation took too long")

        # Verify all payments were created
        self.assertEqual(Payment.objects.filter(user=self.user).count(), 10)

    def test_payment_list_pagination(self):
        """Test payment list pagination for large datasets"""
        # Create 50 test payments
        payments = []
        for i in range(50):
            payment = Payment.objects.create(
                variant="stripe",
                description=f"Test payment {i}",
                total=Decimal(f"{10.00 + i}"),
                currency="USD",
                user=self.user,
                payment_gateway=self.gateway_config,
            )
            payments.append(payment)

        # Test paginated listing
        url = reverse("payment-list")
        response = self.client.get(url)

        # Should return all payments efficiently
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 50)

    def test_payment_logs_performance(self):
        """Test performance of payment logs retrieval"""
        payment = Payment.objects.create(
            variant="stripe",
            description="Performance test payment",
            total=Decimal("29.99"),
            currency="USD",
            user=self.user,
            payment_gateway=self.gateway_config,
        )

        # Create 100 logs for the payment
        for i in range(100):
            PaymentLog.objects.create(
                payment=payment,
                event_type=f"EVENT_{i}",
                message=f"Log message {i}",
                data={"index": i},
            )

        import time

        start_time = time.time()

        url = reverse("payment-logs", kwargs={"pk": payment.id})
        response = self.client.get(url)

        end_time = time.time()
        execution_time = end_time - start_time

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 100)
        self.assertLess(execution_time, 1.0, "Payment logs retrieval took too long")


class EdgeCaseTest(APITestCase):
    """Test edge cases and error conditions"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.token = Token.objects.create(user=self.user)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

        self.gateway_config = PaymentGatewayConfig.objects.create(
            name="stripe", variant="stripe", is_active=True, priority=1
        )

    def test_payment_with_very_long_description(self):
        """Test payment creation with maximum length description"""
        long_description = "A" * 255  # Maximum length

        url = reverse("payment-create-payment")
        data = {
            "amount": "29.99",
            "currency": "USD",
            "description": long_description,
            "gateway": "stripe",
        }

        with patch("payment_gateway.views.Payment.get_form") as mock_url:
            from payments import RedirectNeeded

            mock_url.side_effect = RedirectNeeded(
                "https://checkout.stripe.com/pay/test"
            )
            response = self.client.post(url, data, format="json")
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_payment_with_special_characters(self):
        """Test payment with special characters in fields"""
        url = reverse("payment-create-payment")
        data = {
            "amount": "29.99",
            "currency": "USD",
            "description": "Payment with émojis 🎉 and spéciål chars ñ",
            "gateway": "stripe",
            "order_id": "ORDER-2024-ñ-€-¥",
        }

        with patch("payment_gateway.views.Payment.get_form") as mock_url:
            from payments import RedirectNeeded

            mock_url.side_effect = RedirectNeeded(
                "https://checkout.stripe.com/pay/test"
            )
            response = self.client.post(url, data, format="json")
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_payment_with_different_currencies(self):
        """Test payments with various currencies"""
        currencies = ["USD", "EUR", "GBP", "JPY", "CAD"]

        for currency in currencies:
            url = reverse("payment-create-payment")
            data = {
                "amount": "100.00",
                "currency": currency,
                "description": f"Test payment in {currency}",
                "gateway": "stripe",
            }

            with patch("payment_gateway.views.Payment.get_form") as mock_url:
                from payments import RedirectNeeded

                mock_url.side_effect = RedirectNeeded(
                    "https://checkout.stripe.com/pay/test"
                )
                response = self.client.post(url, data, format="json")
                self.assertEqual(response.status_code, status.HTTP_201_CREATED)
                self.assertEqual(response.data["currency"], currency)

    def test_payment_with_complex_metadata(self):
        """Test payment with complex metadata structure"""
        complex_metadata = {
            "customer": {
                "id": 12345,
                "name": "John Doe",
                "preferences": ["email", "sms"],
            },
            "products": [
                {"id": 1, "name": "Product A", "price": 19.99},
                {"id": 2, "name": "Product B", "price": 10.00},
            ],
            "shipping": {"address": "123 Main St", "method": "express", "cost": 5.99},
            "flags": {"is_gift": True, "requires_signature": False, "priority": None},
        }

        url = reverse("payment-create-payment")
        data = {
            "amount": "35.98",
            "currency": "USD",
            "description": "Complex metadata test",
            "gateway": "stripe",
            "metadata": complex_metadata,
        }

        with patch("payment_gateway.views.Payment.get_form") as mock_url:
            from payments import RedirectNeeded

            mock_url.side_effect = RedirectNeeded(
                "https://checkout.stripe.com/pay/test"
            )
            response = self.client.post(url, data, format="json")
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

            # Verify metadata was stored correctly
            payment = Payment.objects.get(id=response.data["payment_id"])
            self.assertEqual(payment.metadata["customer"]["name"], "John Doe")
            self.assertEqual(len(payment.metadata["products"]), 2)
            self.assertTrue(payment.metadata["flags"]["is_gift"])

    def test_concurrent_payment_operations(self):
        """Test concurrent payment operations"""
        payment = Payment.objects.create(
            variant="stripe",
            description="Concurrent test payment",
            total=Decimal("50.00"),
            currency="USD",
            user=self.user,
            payment_gateway=self.gateway_config,
            status="preauth",
        )

        # Simulate concurrent capture attempts
        with patch("payment_gateway.models.Payment.capture") as mock_capture:
            mock_capture.side_effect = Exception("Payment already captured")

            url = reverse("payment-capture", kwargs={"pk": payment.id})
            response = self.client.post(url)

            # Should handle the exception gracefully
            self.assertEqual(
                response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            self.assertIn("capture failed", response.data["error"])

    def test_payment_state_transitions(self):
        """Test various payment state transitions"""
        payment = Payment.objects.create(
            variant="stripe",
            description="State transition test",
            total=Decimal("25.00"),
            currency="USD",
            user=self.user,
            payment_gateway=self.gateway_config,
        )

        # Test invalid state transitions
        test_cases = [
            ("waiting", "capture"),  # Can't capture waiting payment
            ("error", "capture"),  # Can't capture errored payment
            ("waiting", "refund"),  # Can't refund waiting payment
            ("rejected", "refund"),  # Can't refund rejected payment
        ]

        for status_val, action in test_cases:
            payment.status = status_val
            payment.save()

            if action == "capture":
                url = reverse("payment-capture", kwargs={"pk": payment.id})
            else:  # refund
                url = reverse("payment-refund", kwargs={"pk": payment.id})

            response = self.client.post(url)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_malformed_webhook_data(self):
        """Test webhook handling with malformed data"""
        # Test with invalid JSON
        url = reverse("webhook", kwargs={"variant": "paypal"})
        response = self.client.post(
            url, data="invalid json data", content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)

        # Test with missing required fields
        response = self.client.post(
            url,
            data=json.dumps({"incomplete": "data"}),
            content_type="application/json",
        )
        # Should handle gracefully without crashing
        self.assertEqual(response.status_code, 200)


class MockProviderTest(TestCase):
    """Test payment provider mocking for development/testing"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

        # Create a mock gateway for testing
        self.mock_gateway = PaymentGatewayConfig.objects.create(
            name="mock", variant="mock", is_active=True, priority=0
        )

    @patch("payment_gateway.models.Payment.get_form")
    def test_mock_payment_provider(self, mock_get_form):
        """Test using mock payment provider for testing"""
        from payments import RedirectNeeded

        mock_get_form.side_effect = RedirectNeeded(
            "https://mock-payment-gateway.test/pay/123"
        )

        payment = Payment.objects.create(
            variant="mock",
            description="Mock payment test",
            total=Decimal("19.99"),
            currency="USD",
            user=self.user,
            payment_gateway=self.mock_gateway,
        )

        # Mock provider should return test URL
        with self.assertRaises(RedirectNeeded) as cm:
            payment.get_form()
        self.assertIn("mock-payment-gateway.test", str(cm.exception))

    def test_mock_payment_success_simulation(self):
        """Test simulating successful payment with mock provider"""
        payment = Payment.objects.create(
            variant="mock",
            description="Mock success test",
            total=Decimal("29.99"),
            currency="USD",
            user=self.user,
            payment_gateway=self.mock_gateway,
        )

        # Simulate successful payment
        payment.status = "confirmed"
        payment.save()

        self.assertEqual(payment.status, "confirmed")
        self.assertEqual(payment.total, Decimal("29.99"))

    def test_mock_payment_failure_simulation(self):
        """Test simulating failed payment with mock provider"""
        payment = Payment.objects.create(
            variant="mock",
            description="Mock failure test",
            total=Decimal("39.99"),
            currency="USD",
            user=self.user,
            payment_gateway=self.mock_gateway,
        )

        # Simulate failed payment
        payment.status = "error"
        payment.save()

        PaymentLog.objects.create(
            payment=payment,
            event_type="PAYMENT_FAILED",
            message="Mock payment failure for testing",
            data={"error_code": "MOCK_DECLINE"},
        )

        self.assertEqual(payment.status, "error")
        self.assertTrue(payment.logs.filter(event_type="PAYMENT_FAILED").exists())
