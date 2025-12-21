from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import transaction
from payments import get_payment_model, RedirectNeeded, PaymentError
from .models import Payment, PaymentGatewayConfig, PaymentLog, Plan, PlanPricing
from .serializers import (
    CreatePaymentSerializer,
    PaymentSerializer,
    PaymentGatewayConfigSerializer,
    PaymentLogSerializer,
    PlanSerializer,
    SubscribeSerializer,
)
from .tasks import process_webhook
import logging
from decimal import Decimal
from django.conf import settings
import stripe
from payments.stripe.providers import StripeProviderV3
from payments import PaymentStatus

logger = logging.getLogger(__name__)


class PaymentGatewayViewSet(viewsets.ReadOnlyModelViewSet):
    """List available payment gateways"""

    queryset = PaymentGatewayConfig.objects.filter(is_active=True)
    serializer_class = PaymentGatewayConfigSerializer
    permission_classes = [IsAuthenticated]


class PaymentViewSet(viewsets.ModelViewSet):
    """Handle payment operations"""

    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Payment.objects.filter(user=self.request.user)

    @action(detail=False, methods=["post"])
    def create_payment(self, request):
        """Create a new payment"""
        serializer = CreatePaymentSerializer(data=request.data)
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    gateway_config = PaymentGatewayConfig.objects.get(
                        name=serializer.validated_data["gateway"], is_active=True
                    )

                    payment = Payment.objects.create(
                        variant=gateway_config.variant,
                        description=serializer.validated_data["description"],
                        total=serializer.validated_data["amount"],
                        currency=serializer.validated_data["currency"],
                        user=request.user,
                        order_id=serializer.validated_data.get("order_id"),
                        payment_gateway=gateway_config,
                        metadata=serializer.validated_data.get("metadata", {}),
                    )

                    # Log payment creation
                    PaymentLog.objects.create(
                        payment=payment,
                        event_type="PAYMENT_CREATED",
                        message=f"Payment created with {gateway_config.name}",
                        data={
                            "amount": str(payment.total),
                            "currency": payment.currency,
                        },
                    )

                    # Branch: localstripe (PaymentIntents) vs prod (Checkout Session)
                    if settings.USE_LOCALSTRIPE:
                        provider = StripeProviderV3(
                            api_key=settings.STRIPE_API_KEY,
                            endpoint_secret=settings.STRIPE_WEBHOOK_SECRET,
                            secure_endpoint=False,
                        )
                        amount_decimal = Decimal(
                            str(serializer.validated_data["amount"])
                        )
                        amount_cents = provider.convert_amount(
                            serializer.validated_data["currency"], amount_decimal
                        )
                        intent = stripe.PaymentIntent.create(
                            amount=amount_cents,
                            currency=serializer.validated_data["currency"].lower(),
                            confirm=True,
                            payment_method="pm_card_visa",
                            metadata={
                                "payment_id": str(payment.id),
                                "token": str(payment.token),
                            },
                            # For manual capture testing, set capture_method="manual"
                        )
                        payment.transaction_id = intent["id"]
                        payment.attrs.intent = intent
                        # Update status based on PI state
                        if intent.get("status") == "succeeded":
                            payment.change_status(PaymentStatus.CONFIRMED)
                        elif intent.get("status") == "requires_capture":
                            payment.change_status(PaymentStatus.PREAUTH)
                        else:
                            payment.change_status(PaymentStatus.WAITING)
                        payment.save()

                        PaymentLog.objects.create(
                            payment=payment,
                            event_type="PI_CREATED",
                            message="PaymentIntent created in local mode",
                            data={
                                "intent_id": intent["id"],
                                "status": intent.get("status"),
                            },
                        )

                        return Response(
                            {
                                "payment_id": payment.id,
                                "status": payment.status,
                                "intent_id": intent["id"],
                                "client_secret": intent.get("client_secret"),
                                "amount": payment.total,
                                "currency": payment.currency,
                            },
                            status=status.HTTP_201_CREATED,
                        )
                    else:
                        # Ask provider to create a Checkout Session and get redirect URL
                        try:
                            payment.get_form()
                        except RedirectNeeded as redirect_to:
                            gateway_url = str(redirect_to)

                        return Response(
                            {
                                "payment_id": payment.id,
                                "status": payment.status,
                                "gateway_url": gateway_url,
                                "amount": payment.total,
                                "currency": payment.currency,
                            },
                            status=status.HTTP_201_CREATED,
                        )

            except PaymentGatewayConfig.DoesNotExist:
                return Response(
                    {"error": "Payment gateway not found or inactive"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            except PaymentError as e:
                logger.error(f"Payment creation failed (provider): {str(e)}")
                return Response(
                    {"error": "Payment creation failed with provider"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
            except Exception as e:
                logger.error(f"Payment creation failed: {str(e)}")
                return Response(
                    {"error": "Payment creation failed"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SubscriptionViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"], url_path="plans")
    def plans(self, request):
        qs = Plan.objects.filter(available=True).prefetch_related("pricings")
        return Response(PlanSerializer(qs, many=True).data)

    def _get_or_create_customer(self, user):
        # Lookup by email for simplicity in local mode
        cust = None
        if user.email:
            try:
                found = stripe.Customer.list(email=user.email).data
                if found:
                    cust = found[0]
            except Exception:
                pass
        if not cust:
            cust = stripe.Customer.create(
                email=user.email or None,
                name=getattr(user, "username", None),
                metadata={"user_id": str(user.id)},
            )
        # Attach test payment method for paid plans (safe if already attached)
        try:
            stripe.PaymentMethod.attach(
                "pm_card_visa", customer=cust["id"]
            )  # idempotent
            stripe.Customer.modify(
                cust["id"], invoice_settings={"default_payment_method": "pm_card_visa"}
            )
        except Exception:
            pass
        return cust

    @action(detail=False, methods=["post"], url_path="subscribe")
    def subscribe(self, request):
        serializer = SubscribeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        plan = get_object_or_404(
            Plan, id=serializer.validated_data["plan_id"], available=True
        )
        pricing = plan.pricings.filter(active=True).order_by("-created").first()
        if not pricing or not pricing.stripe_price_id:
            return Response(
                {"error": "Plan pricing unavailable"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        customer = self._get_or_create_customer(request.user)
        # Localstripe uses legacy Plans instead of Prices
        item_key = "plan" if settings.USE_LOCALSTRIPE else "price"
        sub_kwargs = {
            "customer": customer["id"],
            "items": [{item_key: pricing.stripe_price_id}],
            "expand": ["latest_invoice.payment_intent"],
        }
        if pricing.trial_period_days:
            sub_kwargs["trial_period_days"] = pricing.trial_period_days
        if not plan.auto_renew:
            sub_kwargs["cancel_at_period_end"] = True

        subscription = stripe.Subscription.create(**sub_kwargs)
        return Response(
            {
                "subscription_id": subscription.get("id"),
                "status": subscription.get("status"),
                "current_period_end": subscription.get("current_period_end"),
                "plan": PlanSerializer(plan).data,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["post"], url_path="cancel")
    def cancel(self, request):
        subscription_id = request.data.get("subscription_id")
        if not subscription_id:
            return Response(
                {"error": "subscription_id required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        subscription = stripe.Subscription.modify(
            subscription_id, cancel_at_period_end=True
        )
        return Response(
            {"subscription_id": subscription_id, "status": subscription.get("status")}
        )

    @action(detail=False, methods=["get"], url_path="status")
    def status(self, request):
        customer = self._get_or_create_customer(request.user)
        subs = stripe.Subscription.list(
            customer=customer["id"], status="all", expand=["data.items"]
        )
        results = []
        for s in subs.get("data", []):
            item_ids = []
            for it in s.get("items", {}).get("data", []):
                if settings.USE_LOCALSTRIPE:
                    # Local legacy: item may have plan as object or string id
                    pl = it.get("plan")
                    if isinstance(pl, dict) and pl.get("id"):
                        item_ids.append(pl["id"])
                    elif isinstance(pl, str):
                        item_ids.append(pl)
                else:
                    pr = it.get("price")
                    if isinstance(pr, dict) and pr.get("id"):
                        item_ids.append(pr["id"])
            pricing = (
                PlanPricing.objects.filter(stripe_price_id__in=item_ids)
                .select_related("plan")
                .first()
            )
            results.append(
                {
                    "subscription_id": s.get("id"),
                    "status": s.get("status"),
                    "current_period_end": s.get("current_period_end"),
                    "plan": PlanSerializer(pricing.plan).data if pricing else None,
                }
            )
        return Response(results)

    @action(detail=False, methods=["get"], url_path="me/limits")
    def me_limits(self, request):
        """Return today's policy limits for the user: prefer active subscription; fallback to default plan."""
        active_plan = None
        try:
            customer = self._get_or_create_customer(request.user)
            subs = stripe.Subscription.list(
                customer=customer["id"], status="active", expand=["data.items"]
            )
            for s in subs.get("data", []):
                item_ids = []
                for it in s.get("items", {}).get("data", []):
                    if settings.USE_LOCALSTRIPE:
                        pl = it.get("plan")
                        if isinstance(pl, dict) and pl.get("id"):
                            item_ids.append(pl["id"])
                        elif isinstance(pl, str):
                            item_ids.append(pl)
                    else:
                        pr = it.get("price")
                        if isinstance(pr, dict) and pr.get("id"):
                            item_ids.append(pr["id"])
                pricing = (
                    PlanPricing.objects.filter(stripe_price_id__in=item_ids)
                    .select_related("plan")
                    .first()
                )
                if pricing:
                    active_plan = pricing.plan
                    break
        except Exception:
            active_plan = None
        if not active_plan:
            active_plan = Plan.objects.filter(default=True, available=True).first()
        if not active_plan:
            return Response(
                {"error": "No plan available"}, status=status.HTTP_404_NOT_FOUND
            )
        return Response(
            {
                "plan_id": active_plan.id,
                "plan_name": active_plan.name,
                "daily_time_minutes": active_plan.daily_time_minutes,
                "daily_data_mb": active_plan.daily_data_mb,
            }
        )

    @action(detail=True, methods=["post"], url_path="capture", url_name="capture")
    def capture_payment(self, request, pk=None):
        """Capture an authorized payment"""
        payment = self.get_object()

        if payment.status != "preauth":
            return Response(
                {"error": "Payment is not in preauth status"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            payment.capture()
            PaymentLog.objects.create(
                payment=payment,
                event_type="PAYMENT_CAPTURED",
                message="Payment captured successfully",
            )
            return Response({"status": payment.status})
        except Exception as e:
            logger.error(f"Payment capture failed: {str(e)}")
            PaymentLog.objects.create(
                payment=payment,
                event_type="PAYMENT_CAPTURE_FAILED",
                message=f"Payment capture failed: {str(e)}",
            )
            return Response(
                {"error": "Payment capture failed"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["post"], url_path="refund", url_name="refund")
    def refund_payment(self, request, pk=None):
        """Refund a confirmed payment"""
        payment = self.get_object()
        amount = request.data.get("amount")

        if payment.status != "confirmed":
            return Response(
                {"error": "Payment is not confirmed"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            if amount:
                payment.refund(amount=Decimal(amount))
            else:
                payment.refund()

            PaymentLog.objects.create(
                payment=payment,
                event_type="PAYMENT_REFUNDED",
                message=f"Payment refunded: {amount or payment.total}",
            )
            return Response({"status": payment.status})
        except Exception as e:
            logger.error(f"Payment refund failed: {str(e)}")
            PaymentLog.objects.create(
                payment=payment,
                event_type="PAYMENT_REFUND_FAILED",
                message=f"Payment refund failed: {str(e)}",
            )
            return Response(
                {"error": "Payment refund failed"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["get"], url_path="logs", url_name="logs")
    def logs(self, request, pk=None):
        """Get payment logs"""
        payment = self.get_object()
        logs = payment.logs.all()
        serializer = PaymentLogSerializer(logs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"], url_path="success", url_name="success")
    def success(self, request, pk=None):
        """Handle success redirect after Stripe Checkout"""
        payment = self.get_object()
        # Log the redirect event
        PaymentLog.objects.create(
            payment=payment,
            event_type="PAYMENT_SUCCESS_REDIRECT",
            message="User returned from Stripe success URL",
        )
        return Response(
            {
                "payment_id": payment.id,
                "status": payment.status,
                "message": "Payment success redirect received",
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["get"], url_path="failure", url_name="failure")
    def failure(self, request, pk=None):
        """Handle failure/cancel redirect after Stripe Checkout"""
        payment = self.get_object()
        # Log the redirect event
        PaymentLog.objects.create(
            payment=payment,
            event_type="PAYMENT_FAILURE_REDIRECT",
            message="User returned from Stripe failure/cancel URL",
        )
        return Response(
            {
                "payment_id": payment.id,
                "status": payment.status,
                "message": "Payment failure redirect received",
            },
            status=status.HTTP_200_OK,
        )
