from decouple import Config, RepositoryEnv

from .base import *

# Load enviroment
config = Config(RepositoryEnv(BASE_DIR.parent / ".env.prod"))

# Main configuration
SECRET_KEY = config("SECRET_KEY")
DEBUG = config("DEBUG", default=True, cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="*").split(",")
