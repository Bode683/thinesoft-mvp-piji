"""
Base models and mixins for common functionality.
"""
from django.db import models


class TimeStampedModel(models.Model):
    """
    Abstract base model with created_at and updated_at timestamps.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class BaseModel(TimeStampedModel):
    """
    Abstract base model with timestamps and common patterns.
    """
    class Meta:
        abstract = True
