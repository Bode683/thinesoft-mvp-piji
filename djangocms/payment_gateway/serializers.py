from rest_framework import serializers
from .models import Payment, PaymentGatewayConfig, PaymentLog, Plan, PlanPricing
from decimal import Decimal

class PaymentGatewayConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentGatewayConfig
        fields = ['id', 'name', 'variant', 'is_active', 'priority']

class CreatePaymentSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0.01'))
    currency = serializers.CharField(max_length=3, default='USD')
    description = serializers.CharField(max_length=255)
    order_id = serializers.CharField(max_length=100, required=False)
    gateway = serializers.CharField(max_length=50)
    metadata = serializers.JSONField(required=False, default=dict)
    
    def validate_gateway(self, value):
        if not PaymentGatewayConfig.objects.filter(name=value, is_active=True).exists():
            raise serializers.ValidationError(f"Gateway '{value}' is not available or inactive")
        return value

class PaymentSerializer(serializers.ModelSerializer):
    gateway_name = serializers.CharField(source='payment_gateway.name', read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'status', 'variant', 'currency', 'total', 'description',
            'order_id', 'gateway_name', 'created', 'modified', 'metadata'
        ]
        read_only_fields = ['id', 'status', 'created', 'modified']

class PaymentLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentLog
        fields = ['id', 'event_type', 'message', 'data', 'created_at']


class PlanPricingSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlanPricing
        fields = [
            'id', 'amount', 'currency', 'interval', 'trial_period_days',
            'active', 'stripe_price_id', 'created'
        ]


class PlanSerializer(serializers.ModelSerializer):
    pricings = PlanPricingSerializer(many=True, read_only=True)

    class Meta:
        model = Plan
        fields = [
            'id', 'name', 'description', 'default', 'available', 'requires_payment',
            'requires_invoice', 'auto_renew', 'created', 'daily_time_minutes',
            'daily_data_mb', 'stripe_product_id', 'metadata', 'pricings'
        ]


class SubscribeSerializer(serializers.Serializer):
    plan_id = serializers.IntegerField()
