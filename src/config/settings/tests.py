import tempfile

from decouple import Config, RepositoryEnv

from config.settings.base import REST_FRAMEWORK

from .base import *

# -----------------------------------------------------------------------------
# LOAD ENVIRONMENT
# -----------------------------------------------------------------------------
config = Config(RepositoryEnv(BASE_DIR.parent / ".env"))

# -----------------------------------------------------------------------------
# CORE SETTINGS
# -----------------------------------------------------------------------------
SECRET_KEY = config("SECRET_KEY", default="test-secret-key")
DEBUG = config("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = ["*"]
MEDIA_ROOT = tempfile.mkdtemp()

# -----------------------------------------------------------------------------
# SECURITY OPTIMIZATION (FOR SPEED)
# ----------------------------------------------------------------------------
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]
AUTH_PASSWORD_VALIDATORS = []

# -----------------------------------------------------------------------------
# DATABASE (IN-MEMORY)
# -----------------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# -----------------------------------------------------------------------------
# CACHE
# -----------------------------------------------------------------------------
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "tests",
    }
}
REST_FRAMEWORK["NUM_PROXIES"] = config("NUM_PROXIES", default=0, cast=int)
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {
    **REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"],
    "anon": "10000/hour",
    "user": "10000/hour",
    "anon_read": "10000/hour",
    "user_read": "10000/hour",
    "login": "10000/hour",
    "token": "10000/hour",
    "write": "10000/hour",
    "upload_hour": "10000/hour",
    "upload_burst": "10000/min",
    "password_change": "10000/hour",
}

# -----------------------------------------------------------------------------
# REST FRAMEWORK
# -----------------------------------------------------------------------------
REST_FRAMEWORK.update(
    {
        "TEST_REQUEST_RENDERER_CLASSES": (
            "rest_framework_json_api.renderers.JSONRenderer",
            "rest_framework.renderers.JSONRenderer",
            "rest_framework.renderers.MultiPartRenderer",
        ),
        "TEST_REQUEST_DEFAULT_FORMAT": "vnd.api+json",
    }
)

# -----------------------------------------------------------------------------
# METADATA
# -----------------------------------------------------------------------------
API_VERSION = config("API_VERSION", default="1.0")

# -----------------------------------------------------------------------------
# CELERY
# -----------------------------------------------------------------------------
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
