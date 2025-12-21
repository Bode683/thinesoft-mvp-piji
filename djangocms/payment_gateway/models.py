from django.db import models
from django.conf import settings
from payments.models import BasePayment
import uuid


class PaymentGatewayConfig(models.Model):
    """Configuration for different payment gateways"""

    name = models.CharField(max_length=50, unique=True)
    variant = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    priority = models.IntegerField(
        default=0, help_text="Higher number = higher priority"
    )

    class Meta:
        ordering = ["-priority"]

    def __str__(self):
        return f"{self.name} ({'Active' if self.is_active else 'Inactive'})"


class Payment(BasePayment):
    """Extended Payment model with additional fields"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True
    )
    order_id = models.CharField(max_length=100, null=True, blank=True)
    payment_gateway = models.ForeignKey(
        PaymentGatewayConfig, on_delete=models.SET_NULL, null=True
    )
    webhook_received = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict, blank=True)

    def get_failure_url(self):
        return f"http://{self.get_host()}/api/v1/payments/{self.id}/failure/"

    def get_success_url(self):
        return f"http://{self.get_host()}/api/v1/payments/{self.id}/success/"

    def get_host(self):
        from django.conf import settings

        return settings.PAYMENT_HOST


class PaymentLog(models.Model):
    """Log all payment events"""

    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name="logs")
    event_type = models.CharField(max_length=50)
    message = models.TextField()
    data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class Plan(models.Model):
    """Subscription plan definition mapping to a Stripe Product."""

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    default = models.BooleanField(default=False)
    available = models.BooleanField(default=True)
    requires_payment = models.BooleanField(default=True)
    requires_invoice = models.BooleanField(default=True)
    auto_renew = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)

    # Policy limits (optional)
    daily_time_minutes = models.PositiveIntegerField(null=True, blank=True)
    daily_data_mb = models.PositiveIntegerField(null=True, blank=True)

    # Stripe mapping
    stripe_product_id = models.CharField(max_length=128, null=True, blank=True)

    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class PlanPricing(models.Model):
    """Plan pricing mapping to a Stripe Price."""

    INTERVAL_CHOICES = (
        ("day", "day"),
        ("week", "week"),
        ("month", "month"),
        ("year", "year"),
    )

    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name="pricings")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="USD")
    interval = models.CharField(max_length=10, choices=INTERVAL_CHOICES, default="month")
    trial_period_days = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)

    # Stripe mapping
    stripe_price_id = models.CharField(max_length=128, null=True, blank=True)

    class Meta:
        unique_together = ("plan", "currency", "interval", "amount")
        ordering = ["plan__name", "amount"]

    def __str__(self):
        return f"{self.plan.name} {self.amount} {self.currency}/{self.interval}"
