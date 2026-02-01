"""
Subscriber permission classes.
"""
from rest_framework.permissions import BasePermission

from . import selectors


class IsActiveSubscriber(BasePermission):
    """
    User has a valid subscriber profile.

    Subscriber = business state, checked via model:
    - is_active is True
    - Not expired
    """
    message = "You must have an active subscription."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        return selectors.user_is_active_subscriber(request.user)


class IsSubscriber(BasePermission):
    """
    User has a subscriber profile (active or not).
    """
    message = "You must have a subscriber profile."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        return selectors.user_is_subscriber(request.user)


class IsSubscriberOwner(BasePermission):
    """
    User owns the subscriber profile being accessed.
    """
    message = "You can only access your own subscriber profile."

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True

        return obj.user == request.user
