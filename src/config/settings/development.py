from decouple import Config, RepositoryEnv

from .base import *

# -----------------------------------------------------------------------------
# LOAD ENVIROMENT
# -----------------------------------------------------------------------------
config = Config(RepositoryEnv(BASE_DIR.parent / ".env.dev"))

# -----------------------------------------------------------------------------
# CORE SETTINGS
# -----------------------------------------------------------------------------
SECRET_KEY = config("SECRET_KEY", default="django-insecure-dev-key")
DEBUG = config("DEBUG", default=True, cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="localhost,127.0.0.1").split(",")
MEDIA_STORAGE_BACKEND = config("MEDIA_STORAGE_BACKEND", default="local")

# -----------------------------------------------------------------------------
# APPS
# -----------------------------------------------------------------------------
INSTALLED_APPS += ["django_extensions"]

# -----------------------------------------------------------------------------
# METADATA
# -----------------------------------------------------------------------------
API_VERSION = config("API_VERSION", default="1.0")

# -----------------------------------------------------------------------------
# CACHE
# -----------------------------------------------------------------------------

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": config("CACHE_URL", default="redis://redis:6379/2"),
        "TIMEOUT": 300,
        "KEY_PREFIX": "blog",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "IGNORE_EXCEPTIONS": True,
            "SOCKET_CONNECT_TIMEOUT": 5,
            "SOCKET_TIMEOUT": 5,
        },
    }
}

# -----------------------------------------------------------------------------
# CELERY
# -----------------------------------------------------------------------------
CELERY_BROKER_URL = config("CELERY_BROKER_URL", default="redis://redis:6379/0")
CELERY_RESULT_BACKEND = config("CELERY_RESULT_BACKEND", default="redis://redis:6379/1")
