from pathlib import Path
import os, stripe
import dj_database_url
from django_storage_url import dsn_configured_storage_class
from dotenv import load_dotenv

# Load environment variables from .env.local (preferred) and .env as fallback
_ENV_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
load_dotenv(os.path.join(_ENV_ROOT, ".env.local"))
load_dotenv(os.path.join(_ENV_ROOT, ".env"))
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get("SECRET_KEY", "<a string of random characters>")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get("DEBUG") == "True"

# ALLOWED_HOSTS = [os.environ.get('DOMAIN'),]
# if DEBUG:
#     ALLOWED_HOSTS = ["*",]
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


# Application definition

INSTALLED_APPS = [
    "backend",
    "rest_framework",
    "rest_framework.authtoken",  # <-- Add this
    "dj_rest_auth",
    "dj_rest_auth.registration",  # <-- Add this
    "allauth",  # <-- Add this
    "allauth.account",  # <-- Add this
    "allauth.socialaccount",  # <-- Add this
    # optional, but used in most projects
    "djangocms_admin_style",
    "corsheaders",
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
    "allauth.account.middleware.AccountMiddleware",
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
    #'easy_thumbnails.processors.scale_and_crop',
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

# Configure database using DATABASE_URL; fall back to sqlite in memory when no
# environment variable is available, e.g. during Docker build
# DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite://:memory:')
# DATABASES = {'default': dj_database_url.parse(DATABASE_URL)}
# DATABASES = {
#     'default': {
#         'ENGINE': os.environ.get('DJANGO_DB_ENGINE', 'django.db.backends.postgresql_psycopg2'),
#         'NAME': os.environ.get('DJANGO_DB_NAME', 'django_db'),
#         'USER': os.environ.get('DJANGO_DB_USER', 'django_user'),
#         'PASSWORD': os.environ.get('DJANGO_DB_PASSWORD', 'django_pass'),
#         'HOST': os.environ.get('DJANGO_DB_HOST', 'localhost'),
#         'PORT': os.environ.get('DJANGO_DB_PORT', ''),
#     }
# }

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

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
        # "rest_framework.authentication.SessionAuthentication",
    ]
}
AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",  # Django's default
    "allauth.account.auth_backends.AuthenticationBackend",  # allauth's backend
)


# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

if not DEBUG:
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

STATICFILES_DIRS = [  # this are were django staticfiles is looking for sources
    BASE_DIR / "backend" / "static",
]

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(
    BASE_DIR, "staticfiles_collected"
)  # this is were the collected files are placed

# read the setting value from the environment variable. This functionality is
# provided by https://github.com/divio/django-storage-url
DEFAULT_STORAGE_DSN = os.environ.get("DEFAULT_STORAGE_DSN", "/data/media/")
DefaultStorageClass = dsn_configured_storage_class("DEFAULT_STORAGE_DSN")

STORAGES = {
    "default": {
        "BACKEND": "backend.settings.DefaultStorageClass",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        # 'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage',
    },
}

# only required for local file storage and serving, in development
MEDIA_URL = "media/"
MEDIA_ROOT = "/data/media/"

STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles/")

SITE_ID = 1

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

CMS_CONFIRM_VERSION4 = True
DJANGOCMS_VERSIONING_ALLOW_DELETING_VERSIONS = True

ACCOUNT_EMAIL_VERIFICATION = "none"  # Or 'mandatory' or 'optional'
ACCOUNT_LOGIN_METHODS = {"username", "email"}  # or 'email' or 'username_email'
ACCOUNT_SIGNUP_FIELDS = ["email*", "username*", "password1*", "password2*"]


# Payment Gateway Configuration
# --- Local Stripe Configuration ---

USE_LOCALSTRIPE = os.environ.get("USE_LOCALSTRIPE", "False").lower() == "true"

if USE_LOCALSTRIPE:
    # Point the stripe library to the localstripe server (overrideable)
    LOCALSTRIPE_URL = os.environ.get("LOCALSTRIPE_URL", "http://127.0.0.1:8420")
    stripe.api_base = LOCALSTRIPE_URL  # Default localstripe base
    # Some stripe clients also use uploads_base/files_base
    try:
        stripe.uploads_base = LOCALSTRIPE_URL
        stripe.files_base = LOCALSTRIPE_URL
    except Exception:
        pass
    # Use dummy keys for localstripe
    STRIPE_API_KEY = "sk_test_123"
    STRIPE_WEBHOOK_SECRET = "whsec_123"
    # Ensure the Stripe SDK has an API key configured
    stripe.api_key = STRIPE_API_KEY

    print("--- USING LOCALSTRIPE MOCK SERVER ---")
    # Avoid HTTPS redirect issues for webhooks in local mode
    SECURE_SSL_REDIRECT = False

else:
    # Use real Stripe keys from environment variables for production
    STRIPE_API_KEY = os.environ.get("STRIPE_API_KEY")
    STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET")
    # Ensure the Stripe SDK has an API key configured
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

# dj-stripe configuration (local-first; production placeholders)
STRIPE_LIVE_MODE = False
DJSTRIPE_WEBHOOK_SECRET = os.environ.get("DJSTRIPE_WEBHOOK_SECRET", "whsec_123")
DJSTRIPE_USE_NATIVE_JSONFIELD = True
DJSTRIPE_FOREIGN_KEY_TO_FIELD = "id"

# Celery Configuration (for async processing)
CELERY_BROKER_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("REDIS_URL", "redis://localhost:6379/0")
