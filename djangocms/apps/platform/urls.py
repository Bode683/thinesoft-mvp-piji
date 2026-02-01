"""
Platform admin URL configuration.
"""
from django.urls import path

from .views import (
    PlatformStatsView,
    PlatformUserListView,
    PlatformUserDetailView,
    PlatformTenantListView,
    PlatformTenantDetailView,
)

app_name = "platform"

urlpatterns = [
    path("stats/", PlatformStatsView.as_view(), name="stats"),
    path("users/", PlatformUserListView.as_view(), name="user-list"),
    path("users/<int:user_id>/", PlatformUserDetailView.as_view(), name="user-detail"),
    path("tenants/", PlatformTenantListView.as_view(), name="tenant-list"),
    path("tenants/<slug:slug>/", PlatformTenantDetailView.as_view(), name="tenant-detail"),
]
