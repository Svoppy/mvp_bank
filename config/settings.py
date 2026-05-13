import os
import sys
from pathlib import Path

from django.db.backends.signals import connection_created
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


IS_TESTING = "test" in sys.argv
IS_DEPLOY_CHECK = "check" in sys.argv and "--deploy" in sys.argv
SECRET_KEY = os.environ["SECRET_KEY"]
JWT_SECRET = os.environ["JWT_SECRET"]
DEBUG = False if IS_DEPLOY_CHECK else _env_bool("DEBUG", False)
ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if host.strip()
]
TRUST_PROXY_HEADERS = _env_bool("TRUST_PROXY_HEADERS", False)

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "apps.auth_app",
    "apps.loans",
    "apps.audit",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
    "core.middleware.DisableApiCsrfMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
            ]
        },
    }
]

DB_ENGINE = os.environ.get("DB_ENGINE", "postgresql").lower()

if IS_TESTING:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "test_db.sqlite3",
        }
    }
elif DB_ENGINE == "sqlite":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / os.environ.get("SQLITE_PATH", "db.sqlite3"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ["DB_NAME"],
            "USER": os.environ["DB_USER"],
            "PASSWORD": os.environ["DB_PASSWORD"],
            "HOST": os.environ.get("DB_HOST", "127.0.0.1"),
            "PORT": os.environ.get("DB_PORT", "5432"),
        }
    }


def _configure_sqlite_connection(sender, connection, **kwargs) -> None:
    """
    This Windows workspace intermittently fails on disk-backed SQLite journals.
    For the MVP demo we keep SQLite commits in memory instead of writing *.journal files.
    """
    if connection.vendor != "sqlite":
        return

    with connection.cursor() as cursor:
        cursor.execute("PRAGMA journal_mode=MEMORY")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA temp_store=MEMORY")


connection_created.connect(_configure_sqlite_connection)

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = False
USE_TZ = True

# Security: limit request body size to 1 MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 1_048_576
DATA_UPLOAD_MAX_NUMBER_FIELDS = 50
FILE_UPLOAD_MAX_MEMORY_SIZE = 262_144
MAX_LOAN_DOCUMENT_BYTES = int(os.environ.get("MAX_LOAN_DOCUMENT_BYTES", "524288"))
LOAN_EXPORT_CHUNK_SIZE = int(os.environ.get("LOAN_EXPORT_CHUNK_SIZE", "100"))

MEDIA_ROOT = BASE_DIR / "media"
MEDIA_URL = "/media/"

# Security headers
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_REFERRER_POLICY = "same-origin"

# Proxy trust is disabled by default to prevent spoofed forwarded headers.
USE_X_FORWARDED_HOST = TRUST_PROXY_HEADERS
if TRUST_PROXY_HEADERS:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

if (not DEBUG and not IS_TESTING) or IS_DEPLOY_CHECK:
    SESSION_COOKIE_SECURE = _env_bool("SESSION_COOKIE_SECURE", True)
    CSRF_COOKIE_SECURE = _env_bool("CSRF_COOKIE_SECURE", True)
    SECURE_SSL_REDIRECT = _env_bool("SECURE_SSL_REDIRECT", True)
    SECURE_HSTS_SECONDS = int(os.environ.get("SECURE_HSTS_SECONDS", "31536000"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = _env_bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", True)
    SECURE_HSTS_PRELOAD = _env_bool("SECURE_HSTS_PRELOAD", True)
else:
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    SECURE_SSL_REDIRECT = False
    SECURE_HSTS_SECONDS = 0
    SECURE_HSTS_INCLUDE_SUBDOMAINS = False
    SECURE_HSTS_PRELOAD = False

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
        }
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}
