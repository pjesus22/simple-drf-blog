from decouple import Config, RepositoryEnv

from .base import *

# -----------------------------------------------------------------------------
# LOAD ENVIRONMENT
# -----------------------------------------------------------------------------
config = Config(RepositoryEnv(BASE_DIR.parent / ".env.test"))

# -----------------------------------------------------------------------------
# CORE SETTINGS
# -----------------------------------------------------------------------------
SECRET_KEY = config("SECRET_KEY", default="test-secret-key")
DEBUG = False
ALLOWED_HOSTS = ["*"]

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
SERVE_DOCS = config("SERVE_DOCS", default=True, cast=bool)
