# config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Auto-Form API"
    DEBUG: bool = False
    VERSION: str = "1.0.0"
    MODEL_PATH: str = "./models/field_matcher"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB

    class Config:
        env_file = ".env"

settings = Settings()