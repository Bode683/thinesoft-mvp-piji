"""
Django settings package.

By default, uses development settings.
Set DJANGO_ENV to 'production' or 'prod' for production.
"""
import os

# Default to development settings
env = os.environ.get("DJANGO_ENV", "dev")

if env in ("prod", "production"):
    from .prod import *
else:
    from .dev import *
