from decouple import Config, RepositoryEnv

from .base import *

# Load enviroment
config = Config(RepositoryEnv(BASE_DIR.parent / ".env.prod"))

# Encryption keys
ENCRYPTION_KEYS = {
    1: config("ENCRYPTION_KEY_V1", default=""),
}
CURRENT_KEY_VERSION = config("ENCRYPTION_ACTIVE_VERSION", default=1, cast=int)

# Main configuration
SECRET_KEY = config("SECRET_KEY")
DEBUG = config("DEBUG", default=True, cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="*").split(",")
