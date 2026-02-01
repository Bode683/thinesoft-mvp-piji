"""
Common utility functions.
"""
import re
from django.utils.text import slugify as django_slugify


def generate_unique_slug(model_class, base_value: str, slug_field: str = "slug") -> str:
    """
    Generate a unique slug for a model instance.

    Args:
        model_class: The Django model class
        base_value: The base string to slugify
        slug_field: The name of the slug field (default: "slug")

    Returns:
        A unique slug string
    """
    base_slug = django_slugify(base_value)
    slug = base_slug
    counter = 1

    while model_class.objects.filter(**{slug_field: slug}).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1

    return slug
