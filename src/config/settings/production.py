from decouple import Config, RepositoryEnv
import sentry_sdk

from .base import *

# -----------------------------------------------------------------------------
# LOAD ENVIROMENT
# -----------------------------------------------------------------------------
config = Config(RepositoryEnv(BASE_DIR.parent / ".env.prod"))

# -----------------------------------------------------------------------------
# CORE SETTINGS
# -----------------------------------------------------------------------------
SECRET_KEY = config("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY must be set in production environment!")

DEBUG = config("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = config(
    "ALLOWED_HOSTS", cast=lambda v: [s.strip() for s in v.split(",")]
)
MEDIA_STORAGE_BACKEND = config("MEDIA_STORAGE_BACKEND", default="local")

# -----------------------------------------------------------------------------
# STORAGE
# -----------------------------------------------------------------------------
# S3
AWS_ACCESS_KEY_ID = config("AWS_ACCESS_KEY_ID", cast=str, default=None)
AWS_SECRET_ACCESS_KEY = config("AWS_SECRET_ACCESS_KEY", cast=str, default=None)
AWS_STORAGE_BUCKET_NAME = config("AWS_STORAGE_BUCKET_NAME", cast=str, default=None)
AWS_S3_REGION_NAME = config("AWS_S3_REGION_NAME", cast=str, default=None)

# Google
GS_BUCKET_NAME = config("GS_BUCKET_NAME", cast=str, default=None)
GOOGLE_APPLICATION_CREDENTIALS = config(
    "GOOGLE_APPLICATION_CREDENTIALS", cast=str, default=None
)

# -----------------------------------------------------------------------------
# SECURITY SETTINGS
# -----------------------------------------------------------------------------
SECURE_SSL_REDIRECT = False
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# -----------------------------------------------------------------------------
# HSTS SETTINGS
# -----------------------------------------------------------------------------
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# -----------------------------------------------------------------------------
# LOGGING
# -----------------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}

# -----------------------------------------------------------------------------
# METADATA
# -----------------------------------------------------------------------------
API_VERSION = config("API_VERSION", default="1.0")


# -----------------------------------------------------------------------------
# MONITORING
# -----------------------------------------------------------------------------

sentry_sdk.init(
    dsn=config("SENTRY_DSN", default=""),
    enviroment=config("ENVIRONMENT", default="production"),
    traces_sample_rate=0.1,
)
