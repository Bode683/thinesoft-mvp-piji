"""
Custom exceptions for the application.
"""
from rest_framework import status
from rest_framework.exceptions import APIException


class ServiceException(APIException):
    """Base exception for service layer errors."""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "A service error occurred."
    default_code = "service_error"


class PermissionDeniedException(APIException):
    """Raised when a user lacks permission for an action."""
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "You do not have permission to perform this action."
    default_code = "permission_denied"


class TenantNotFoundException(APIException):
    """Raised when a tenant is not found."""
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Tenant not found."
    default_code = "tenant_not_found"


class MembershipNotFoundException(APIException):
    """Raised when a membership is not found."""
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Membership not found."
    default_code = "membership_not_found"


class SubscriberNotFoundException(APIException):
    """Raised when a subscriber is not found."""
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Subscriber profile not found."
    default_code = "subscriber_not_found"
