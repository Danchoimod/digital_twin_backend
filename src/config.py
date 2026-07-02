import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "FastAPI GCP Twin Backend"
    DEBUG: bool = False
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api/v1"
    
    # Database Settings
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "twin_db"
    
    # GCP Settings
    GCP_PROJECT_ID: Optional[str] = None
    GCP_STORAGE_BUCKET: Optional[str] = None
    GCP_PUBSUB_TOPIC: Optional[str] = None
    GCP_CREDENTIALS_PATH: Optional[str] = None

    # CORS Origins
    CORS_ORIGINS: List[str] = ["*"]
    
    # JWT Settings (for auth)
    JWT_SECRET_KEY: str = "supersecretkeychangeinproduction"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Allow overriding settings using an optional .env file
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
