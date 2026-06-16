# File: settings.py. Description: Application configuration management. Consists of: Pydantic BaseSettings class loading environment variables.
import os
from pydantic_settings import BaseSettings

# Calculate the absolute path to the backend/.env file relative to this settings.py file
_base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
_env_file = os.path.join(_base_dir, ".env")


class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    TEMPORAL_HOST: str = "localhost:7233"
    TEMPORAL_TASK_QUEUE: str = "billing-tasks"

    model_config = {"env_file": _env_file, "extra": "ignore"}


settings = Settings()
