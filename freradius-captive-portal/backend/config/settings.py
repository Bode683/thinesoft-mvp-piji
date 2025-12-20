from dotenv import load_dotenv
from typing import Optional
from pydantic import BaseSettings
from functools import lru_cache

load_dotenv()

class Settings(BaseSettings):
    RADIUS_SERVER: str = "freeradius"
    RADIUS_SECRET: str = "testing123"
    DATABASE_URL: str = "postgresql://radius:radiuspass@postgres:5432/radius"
    
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"

settings = Settings()

@lru_cache()
def get_settings():
    return settings
