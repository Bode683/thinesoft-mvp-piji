from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
import stripe
from django.views import View
from django.conf import settings
from payments import get_payment_model
import json
import logging
from django.utils.module_loading import import_string

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name="dispatch")
@method_decorator(require_POST, name="dispatch")
class WebhookView(View):
    """Handle payment webhooks from different providers"""

    def post(self, request, variant):
        """Process webhook based on payment variant"""
        try:
            if variant == "stripe":
                return self.handle_stripe_webhook(request)
            elif variant == "paypal":
                return self.handle_paypal_webhook(request)
            else:
                logger.warning(f"Unknown webhook variant: {variant}")
                return HttpResponseBadRequest("Unknown webhook variant")

        except Exception as e:
            logger.error(f"Webhook processing failed: {str(e)}")
            return HttpResponseBadRequest("Webhook processing failed")

    def handle_stripe_webhook(self, request):
        """Handle Stripe webhooks.

        - Local (USE_LOCALSTRIPE=True): process PaymentIntent events without signature
          using metadata.payment_id to locate the Payment.
        - Prod: delegate to StripeProviderV3 which verifies signature and processes
          Checkout Session events.
        """

        # Local mode: accept JSON body and handle payment_intent.*
        if settings.USE_LOCALSTRIPE:
            try:
                event = json.loads(request.body)
            except json.JSONDecodeError:
                return HttpResponseBadRequest("Invalid JSON payload")

            event_type = event.get("type")
            data_object = (event.get("data") or {}).get("object") or {}
            metadata = data_object.get("metadata") or {}
            payment_id = metadata.get("payment_id")

            # Only enforce payment_id for PaymentIntent events; other localstripe
            # events (product/plan/customer/subscription/invoice) are acknowledged.
            if not (event_type or "").startswith("payment_intent."):
                logger.info(f"Localstripe non-PI event received: {event_type}")
                return HttpResponse(status=200)

            if not payment_id:
                logger.warning("Localstripe webhook missing metadata.payment_id for PaymentIntent event")
                return HttpResponseBadRequest("Missing payment_id")

            PaymentModel = get_payment_model()
            try:
                payment = PaymentModel.objects.get(id=payment_id)
            except PaymentModel.DoesNotExist:
                logger.warning(f"Payment with id {payment_id} not found")
                return HttpResponseBadRequest("Payment not found")

            # Store latest intent payload
            try:
                payment.attrs.intent = data_object
            except Exception:
                pass

            # Update status by PI events
            try:
                from payments import PaymentStatus

                if event_type == "payment_intent.succeeded":
                    payment.change_status(PaymentStatus.CONFIRMED)
                elif event_type == "payment_intent.payment_failed":
                    payment.change_status(PaymentStatus.ERROR)
                elif event_type == "payment_intent.canceled":
                    payment.change_status(PaymentStatus.REJECTED)
                payment.save()
            except Exception as e:
                logger.error(f"Error updating payment from PI webhook: {e}")
                return HttpResponseBadRequest("Webhook processing failed")

            return HttpResponse(status=200)

        # Prod mode: use provider to verify signature and process
        try:
            provider_path, provider_kwargs = settings.PAYMENT_VARIANTS["stripe"]
            ProviderClass = import_string(provider_path)
            provider = ProviderClass(**provider_kwargs)

            event = provider.return_event_payload(request)

            # Extract client_reference_id (maps to Payment.token)
            try:
                token = event["data"]["object"]["client_reference_id"]
            except Exception:
                logger.warning("Stripe webhook missing client_reference_id")
                return HttpResponseBadRequest("Missing client_reference_id")

            PaymentModel = get_payment_model()
            try:
                payment = PaymentModel.objects.get(token=token)
            except PaymentModel.DoesNotExist:
                logger.warning(f"Payment with token {token} not found")
                return HttpResponseBadRequest("Payment not found")

            response = provider.process_data(payment, request)
            return response

        except stripe.error.SignatureVerificationError:
            return HttpResponseBadRequest("Invalid signature")
        except ValueError:
            return HttpResponseBadRequest("Invalid payload")
        except Exception as e:
            logger.error(f"Stripe webhook error: {e}")
            return HttpResponseBadRequest("Webhook processing failed")

    def handle_paypal_webhook(self, request):
        """Handle PayPal webhooks"""
        # PayPal webhook verification logic here
        data = json.loads(request.body)
        self.process_paypal_event(data)
        return HttpResponse(status=200)

    def process_stripe_event(self, event):
        """Process Stripe webhook events"""
        if event["type"] == "payment_intent.succeeded":
            # Handle successful payment
            payment_intent = event["data"]["object"]
            # Update payment status
            # Send notification
            pass
        # Add more event handlers as needed

    def process_paypal_event(self, data):
        """Process PayPal webhook events"""
        event_type = data.get("event_type")
        if event_type == "PAYMENT.CAPTURE.COMPLETED":
            # Handle completed payment
            pass
        # Add more event handlers as needed
