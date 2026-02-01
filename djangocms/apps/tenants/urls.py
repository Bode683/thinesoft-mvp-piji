"""
Tenant URL configuration.
"""
from django.urls import path

from .views import (
    TenantListView,
    TenantDetailView,
    TenantMemberListView,
    TenantMemberDetailView,
    LeaveTenantView,
)
from apps.subscribers.views import (
    TenantSubscriberListView,
    TenantSubscriberDetailView,
    ExtendSubscriptionView,
)

app_name = "tenants"

urlpatterns = [
    path("", TenantListView.as_view(), name="tenant-list"),
    path("<slug:slug>/", TenantDetailView.as_view(), name="tenant-detail"),
    path("<slug:slug>/members/", TenantMemberListView.as_view(), name="member-list"),
    path(
        "<slug:slug>/members/<int:membership_id>/",
        TenantMemberDetailView.as_view(),
        name="member-detail"
    ),
    path("<slug:slug>/leave/", LeaveTenantView.as_view(), name="leave-tenant"),
    # Subscriber endpoints (tenant-scoped)
    path(
        "<slug:slug>/subscribers/",
        TenantSubscriberListView.as_view(),
        name="subscriber-list"
    ),
    path(
        "<slug:slug>/subscribers/<int:subscriber_id>/",
        TenantSubscriberDetailView.as_view(),
        name="subscriber-detail"
    ),
    path(
        "<slug:slug>/subscribers/<int:subscriber_id>/extend/",
        ExtendSubscriptionView.as_view(),
        name="subscriber-extend"
    ),
]
