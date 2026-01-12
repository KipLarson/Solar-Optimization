"""Application configuration"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""
    
    # API settings
    app_name: str = "Solar + Storage Optimization API"
    app_version: str = "0.1.0"
    debug: bool = False
    
    # Redis settings (for Celery)
    redis_url: str = "redis://localhost:6379/0"
    
    # Celery settings
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"
    
    # File upload settings
    max_upload_size: int = 10 * 1024 * 1024  # 10 MB
    upload_folder: str = "uploads"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
