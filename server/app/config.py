import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Custom Messenger Server"
    VERSION: str = "1.0.0"
    DEBUG: bool = True

    DATABASE_URL: str = "sqlite+aiosqlite:///./messenger.db"

    SECRET_KEY: str = os.environ.get(
        "SECRET_KEY", "change-me-in-production-use-a-strong-random-key"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30  # 30 days
    ALGORITHM: str = "HS256"

    MEDIA_DIR: str = "./media"
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50 MB

    HOST: str = "0.0.0.0"
    PORT: int = 8443

    # SMS verification (stub — replace with real provider)
    SMS_PROVIDER: str = "stub"

    class Config:
        env_file = ".env"


settings = Settings()
