# Local auth configuration overrides/settings
from src.config import settings

AUTH_SECRET_KEY = settings.JWT_SECRET_KEY
AUTH_ALGORITHM = settings.JWT_ALGORITHM
TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
