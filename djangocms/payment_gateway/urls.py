from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PaymentViewSet, PaymentGatewayViewSet, SubscriptionViewSet
from .webhooks import WebhookView

router = DefaultRouter()
router.register(r"gateways", PaymentGatewayViewSet, basename="gateway")
router.register(r"payments", PaymentViewSet, basename="payment")
router.register(r"subscriptions", SubscriptionViewSet, basename="subscription")

urlpatterns = [
    path("", include(router.urls)),
    path("webhooks/<str:variant>/", WebhookView.as_view(), name="webhook"),
]
