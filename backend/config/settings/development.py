from decouple import Config, RepositoryEnv

from .base import *

# Load enviroment
config = Config(RepositoryEnv(BASE_DIR.parent / ".env.dev"))


# Main configuration
SECRET_KEY = config("SECRET_KEY")
DEBUG = config("DEBUG", default=True, cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="*").split(",")
API_VERSION = config("API_VERSION", default="1.0")
