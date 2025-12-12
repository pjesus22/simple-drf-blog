from decouple import Config, RepositoryEnv

from .base import *

# Load enviroment
config = Config(RepositoryEnv(BASE_DIR.parent / ".env.test"))


# Main configuration
SECRET_KEY = config("SECRET_KEY")
DEBUG = False
TEMPLATE_DEBUG = False
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="*").split(",")
API_VERSION = config("API_VERSION", default="1.0")

# Security
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]
AUTH_PASSWORD_VALIDATORS = []

# Database
DATABASES['default']['NAME'] = ':memory:'

# Logging
LOGGING_CONFIG = None

# Email
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Caches
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}
