"""
Subscriber URL configuration.
"""
from django.urls import path

from .views import MySubscriberView

app_name = "subscribers"

# Note: Tenant-scoped subscriber URLs are defined in tenants/urls.py
# These are user-facing subscriber endpoints
urlpatterns = [
    path("me/", MySubscriberView.as_view(), name="my-subscriber"),
]
