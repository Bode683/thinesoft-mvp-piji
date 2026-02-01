"""
Django base settings - shared across all environments.
"""
from pathlib import Path
import os
import stripe
import dj_database_url
from django_storage_url import dsn_configured_storage_class
from dotenv import load_dotenv

# Load environment variables from .env.local (preferred) and .env as fallback
_ENV_ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "..")
load_dotenv(os.path.join(_ENV_ROOT, ".env.local"))
load_dotenv(os.path.join(_ENV_ROOT, ".env"))

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get("SECRET_KEY", "<a string of random characters>")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get("DEBUG") == "True"

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "172.17.0.1",  # default Docker bridge IP for host, from containers
    "host.docker.internal",  # Docker-provided host alias (Linux requires extra flag)
    "api.theddt.local",  # Traefik routing hostname
]

CORS_ALLOWED_ORIGINS = ["http://localhost:5173", "http://api.theddt.local"]
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = ["http://localhost:5173", "http://api.theddt.local"]

# Redirect to HTTPS by default, unless explicitly disabled
SECURE_SSL_REDIRECT = os.environ.get("SECURE_SSL_REDIRECT") != "False"

X_FRAME_OPTIONS = "SAMEORIGIN"

# Login URLs - standard Django admin login
LOGIN_URL = '/admin/login/'
LOGIN_REDIRECT_URL = '/admin/'
LOGOUT_REDIRECT_URL = '/admin/'

# Session Configuration
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = False  # Set to True when using HTTPS


# Custom User Model
AUTH_USER_MODEL = "identity.User"


# Application definition
INSTALLED_APPS = [
    "backend",
    "rest_framework",
    "rest_framework.authtoken",
    "drf_spectacular",  # OpenAPI 3.0 schema generation
    # optional, but used in most projects
    "djangocms_admin_style",
    "corsheaders",
    # Keycloak Authentication
    "drf_keycloak_auth",  # API JWT authentication
    # Domain-driven apps
    "apps.common",
    "apps.identity",
    "apps.tenants",
    "apps.subscribers",
    "apps.platform",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "whitenoise.runserver_nostatic",  # http://whitenoise.evans.io/en/stable/django.html#using-whitenoise-in-development
    "django.contrib.staticfiles",
    "django.contrib.sites",
    # key django CMS modules
    "cms",
    "menus",
    "treebeard",
    "sekizai",
    # Django Filer - optional, but used in most projects
    "filer",
    "easy_thumbnails",
    # the default publishing implementation - optional, but used in most projects
    "djangocms_versioning",
    # the default alias content - optional, but used in most projects
    "djangocms_alias",
    "parler",
    # the next-gen text editor - optional, but used in most projects
    "djangocms_text",
    # link support
    "djangocms_link",
    # optional django CMS frontend modules
    "djangocms_frontend",
    "djangocms_frontend.contrib.accordion",
    "djangocms_frontend.contrib.alert",
    "djangocms_frontend.contrib.badge",
    "djangocms_frontend.contrib.card",
    "djangocms_frontend.contrib.carousel",
    "djangocms_frontend.contrib.collapse",
    "djangocms_frontend.contrib.content",
    "djangocms_frontend.contrib.grid",
    "djangocms_frontend.contrib.jumbotron",
    "djangocms_frontend.contrib.link",
    "djangocms_frontend.contrib.listgroup",
    "djangocms_frontend.contrib.media",
    "djangocms_frontend.contrib.icon",
    "djangocms_frontend.contrib.image",
    "djangocms_frontend.contrib.tabs",
    "djangocms_frontend.contrib.utilities",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "cms.middleware.user.CurrentUserMiddleware",
    "cms.middleware.page.CurrentPageMiddleware",
    "cms.middleware.toolbar.ToolbarMiddleware",
    "cms.middleware.language.LanguageCookieMiddleware",
]

ROOT_URLCONF = "backend.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.media",
                "django.template.context_processors.csrf",
                "django.template.context_processors.tz",
                "django.template.context_processors.i18n",
                "cms.context_processors.cms_settings",
                "sekizai.context_processors.sekizai",
            ],
        },
    },
]

THUMBNAIL_PROCESSORS = (
    "easy_thumbnails.processors.colorspace",
    "easy_thumbnails.processors.autocrop",
    "filer.thumbnail_processors.scale_and_crop_with_subject_location",
    "easy_thumbnails.processors.filters",
)

CMS_TEMPLATES = [
    # Default template that extend base.html, to be used with Bootstrap 5
    ("bootstrap5.html", "Bootstrap 5 Demo"),
    # a minimal template to get started with
    ("minimal.html", "Minimal template"),
    ("whitenoise-static-files-demo.html", "Static File Demo"),
]

WSGI_APPLICATION = "backend.wsgi.application"


# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases
DATABASES = {
    "default": {
        "ENGINE": os.environ.get("SQL_ENGINE", "django.db.backends.sqlite3"),
        "NAME": os.environ.get("SQL_DATABASE", BASE_DIR / "db.sqlite3"),
        "USER": os.environ.get("SQL_USER", "user"),
        "PASSWORD": os.environ.get("SQL_PASSWORD", "password"),
        "HOST": os.environ.get("SQL_HOST", "localhost"),
        "PORT": os.environ.get("SQL_PORT", 5432),
    }
}


# REST Framework - JWT ONLY for API
REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "apps.identity.authentication.KeycloakJWTAuthentication",  # Primary: JWT bearer tokens
        # NO SessionAuthentication for API - JWT only
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "apps.common.pagination.StandardPagination",
    "PAGE_SIZE": 20,
}


# drf-spectacular - OpenAPI 3.0 Configuration
SPECTACULAR_SETTINGS = {
    "TITLE": "Django CMS Multi-Tenant API",
    "DESCRIPTION": """
## Authentication Strategy

This API uses **dual authentication**:

### REST API Endpoints (`/api/*`)
- **JWT tokens from Keycloak** (Bearer authentication)
- Obtain token from Keycloak, then include: `Authorization: Bearer <token>`
- After authentication, `request.auth_context` provides:
  - `keycloak_id` - User's unique Keycloak identifier
  - `email` - User's email address
  - `realm_roles` - Platform-level roles from Keycloak
  - `is_platform_admin()` - Check if user has platform admin role

### Django Admin (`/admin/`)
- **Session-based** (username/password)
- Not documented in this API spec

## Authorization Model

### Platform-Level (from JWT realm roles)
- `platform_admin` - Cross-tenant administrator with system-wide access

### Tenant-Level (from database)
- `owner` - Full control over tenant, can manage all members and settings
- `admin` - Can manage members and subscribers within the tenant
- `member` - Read-only access to tenant resources

### Subscriber State (business model, not a role)
- Active subscriber status is checked via `Subscriber` model
- Not a permission role - it's a business entity with lifecycle

See individual endpoint documentation for required permissions.

## Multi-Tenancy

Most endpoints are **tenant-scoped** using the `slug` parameter.
Users can only access resources within tenants where they have membership.

Platform admins can access cross-tenant data via `/api/v1/platform/*` endpoints.
""",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,

    # JWT auth (Keycloak)
    "APPEND_COMPONENTS": {
        "securitySchemes": {
            "bearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": (
                    "Keycloak-issued JWT access token.\n\n"
                    "**How to obtain:**\n"
                    "1. Authenticate with Keycloak (web or mobile)\n"
                    "2. Copy the `access_token` from the response\n"
                    "3. Click **Authorize** below\n"
                    "4. Enter: `Bearer <access_token>`\n\n"
                    "**Token structure:**\n"
                    "```json\n"
                    '{\n'
                    '  "sub": "550e8400-e29b-41d4-a716-446655440000",\n'
                    '  "preferred_username": "john@example.com",\n'
                    '  "email": "john@example.com",\n'
                    '  "realm_access": {"roles": ["platform_admin"]}\n'
                    "}\n"
                    "```"
                ),
            }
        }
    },
    "SECURITY": [{"bearerAuth": []}],

    # Organization
    "TAGS": [
        {"name": "Authentication", "description": "User authentication and profile endpoints"},
        {"name": "Tenants", "description": "Multi-tenant organization management"},
        {"name": "Members", "description": "Tenant membership management"},
        {"name": "Subscribers", "description": "Subscriber lifecycle and subscription management"},
        {"name": "Platform", "description": "Platform administration (cross-tenant, requires platform_admin)"},
    ],

    # Component organization
    "COMPONENT_SPLIT_REQUEST": True,
    "SCHEMA_PATH_PREFIX": "/api/v1",

    # Misc
    "DISABLE_ERRORS_AND_WARNINGS": False,
}


AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",  # Django's default
)


# Keycloak Configuration
KEYCLOAK_SERVER_URL = os.environ.get("KEYCLOAK_SERVER_URL", "http://keycloak:8080")
KEYCLOAK_REALM = os.environ.get("KEYCLOAK_REALM", "theddt")
KEYCLOAK_CLIENT_ID = os.environ.get("KEYCLOAK_CLIENT_ID", "djangocms-client")
KEYCLOAK_CLIENT_SECRET = os.environ.get("KEYCLOAK_CLIENT_SECRET", "")

# drf-keycloak-auth Configuration (for API JWT authentication)
KEYCLOAK_CONFIG = {
    "KEYCLOAK_SERVER_URL": KEYCLOAK_SERVER_URL,
    "KEYCLOAK_REALM": KEYCLOAK_REALM,
    "KEYCLOAK_CLIENT_ID": KEYCLOAK_CLIENT_ID,
    "KEYCLOAK_CLIENT_SECRET_KEY": KEYCLOAK_CLIENT_SECRET,
    # Token validation settings
    "KEYCLOAK_AUDIENCE": KEYCLOAK_CLIENT_ID,
    "KEYCLOAK_ISSUER": f"{KEYCLOAK_SERVER_URL}/realms/{KEYCLOAK_REALM}",
    # Permission settings
    "KEYCLOAK_REALM_ROLES_CLAIM": "realm_roles",
    "KEYCLOAK_CLIENT_ROLES_CLAIM": f"resource_access.{KEYCLOAK_CLIENT_ID}.roles",
    # User sync settings (from JWT claims)
    "KEYCLOAK_SYNC_USERNAME_CLAIM": "preferred_username",
    "KEYCLOAK_SYNC_EMAIL_CLAIM": "email",
    "KEYCLOAK_SYNC_FIRST_NAME_CLAIM": "given_name",
    "KEYCLOAK_SYNC_LAST_NAME_CLAIM": "family_name",
    # Token verification (always enable in production)
    "KEYCLOAK_VERIFY_SIGNATURE": True,
    "KEYCLOAK_VERIFY_AUDIENCE": True,
    "KEYCLOAK_VERIFY_EXPIRATION": True,
}

# JWKS Caching
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    },
    "jwks": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "TIMEOUT": 300,
    }
}


# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/
LANGUAGE_CODE = "en"

LANGUAGES = [
    ("en", "English"),
]

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/
STATICFILES_DIRS = [
    BASE_DIR / "backend" / "static",
]

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles/")

# read the setting value from the environment variable
DEFAULT_STORAGE_DSN = os.environ.get("DEFAULT_STORAGE_DSN", "/data/media/")
DefaultStorageClass = dsn_configured_storage_class("DEFAULT_STORAGE_DSN")

STORAGES = {
    "default": {
        "BACKEND": "backend.settings.base.DefaultStorageClass",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# only required for local file storage and serving, in development
MEDIA_URL = "media/"
MEDIA_ROOT = "/data/media/"

SITE_ID = 1

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

CMS_CONFIRM_VERSION4 = True
DJANGOCMS_VERSIONING_ALLOW_DELETING_VERSIONS = True

ACCOUNT_EMAIL_VERIFICATION = "none"
ACCOUNT_LOGIN_METHODS = {"username", "email"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "username*", "password1*", "password2*"]


# Payment Gateway Configuration
USE_LOCALSTRIPE = os.environ.get("USE_LOCALSTRIPE", "False").lower() == "true"

if USE_LOCALSTRIPE:
    LOCALSTRIPE_URL = os.environ.get("LOCALSTRIPE_URL", "http://127.0.0.1:8420")
    stripe.api_base = LOCALSTRIPE_URL
    try:
        stripe.uploads_base = LOCALSTRIPE_URL
        stripe.files_base = LOCALSTRIPE_URL
    except Exception:
        pass
    STRIPE_API_KEY = "sk_test_123"
    STRIPE_WEBHOOK_SECRET = "whsec_123"
    stripe.api_key = STRIPE_API_KEY
    SECURE_SSL_REDIRECT = False
else:
    STRIPE_API_KEY = os.environ.get("STRIPE_API_KEY")
    STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET")
    stripe.api_key = STRIPE_API_KEY

# Configure django-payments
if USE_LOCALSTRIPE:
    PAYMENT_VARIANTS = {
        "stripe": (
            "payments.stripe.providers.StripeProviderV3",
            {
                "api_key": STRIPE_API_KEY,
                "endpoint_secret": STRIPE_WEBHOOK_SECRET,
                "secure_endpoint": False,
            },
        )
    }
else:
    PAYMENT_VARIANTS = {
        "stripe": (
            "payments.stripe.providers.StripeProviderV3",
            {
                "api_key": STRIPE_API_KEY,
                "endpoint_secret": STRIPE_WEBHOOK_SECRET,
                "secure_endpoint": True,
            },
        )
    }

PAYMENT_HOST = os.getenv("PAYMENT_HOST", "localhost:8000")
PAYMENT_USES_SSL = os.getenv("PAYMENT_USES_SSL", "False").lower() == "true"

# dj-stripe configuration
STRIPE_LIVE_MODE = False
DJSTRIPE_WEBHOOK_SECRET = os.environ.get("DJSTRIPE_WEBHOOK_SECRET", "whsec_123")
DJSTRIPE_USE_NATIVE_JSONFIELD = True
DJSTRIPE_FOREIGN_KEY_TO_FIELD = "id"

# Celery Configuration
CELERY_BROKER_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("REDIS_URL", "redis://localhost:6379/0")
