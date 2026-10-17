import os
import logging
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    APP_NAME: str = "Baalaji Pharmacy Management System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Database Settings: Default to MySQL, supports fallback to SQLite
    DB_TYPE: str = os.getenv("DB_TYPE", "mysql")  # "mysql" or "sqlite"
    MYSQL_HOST: str = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT: int = int(os.getenv("MYSQL_PORT", 3306))
    MYSQL_USER: str = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DB: str = os.getenv("MYSQL_DB", "pharmacy_db")
    
    # Explicit DATABASE_URL if provided
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        f"mysql+pymysql://{os.getenv('MYSQL_USER', 'root')}:{os.getenv('MYSQL_PASSWORD', '')}@{os.getenv('MYSQL_HOST', 'localhost')}:{os.getenv('MYSQL_PORT', 3306)}/{os.getenv('MYSQL_DB', 'pharmacy_db')}"
    )
    
    # JWT Authentication
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "baalaji-super-secure-jwt-secret-key-2026-rx-pharmacy")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 720  # 12 hours
    
    # CORS
    CORS_ORIGINS: List[str] = ["*"]
    
    # Base paths
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    MEDIA_DIR: str = os.path.join(
        "/tmp", "baalaji", "media"
    ) if os.getenv("VERCEL") else os.path.join(BASE_DIR, "media")
    INVOICES_DIR: str = os.path.join(MEDIA_DIR, "invoices")
    PURCHASE_BILLS_DIR: str = os.path.join(MEDIA_DIR, "purchase_bills")
    EXPORTS_DIR: str = os.path.join(MEDIA_DIR, "exports")
    TEMPLATES_DIR: str = os.path.join(MEDIA_DIR, "templates")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()

logger = logging.getLogger("pharmacy_config")

if os.getenv("VERCEL"):
    if not os.getenv("DATABASE_URL"):
        logger.warning(
            "DATABASE_URL not set in Vercel environment variables. "
            "Falling back to /tmp/pharmacy.db for preview/demo. For persistent storage, set DATABASE_URL in Vercel Project Settings."
        )

# Ensure media folders exist (safely catch any read-only filesystem issues)
try:
    os.makedirs(settings.INVOICES_DIR, exist_ok=True)
    os.makedirs(settings.PURCHASE_BILLS_DIR, exist_ok=True)
    os.makedirs(settings.EXPORTS_DIR, exist_ok=True)
    os.makedirs(settings.TEMPLATES_DIR, exist_ok=True)
except OSError as e:
    logger.warning(f"Could not create media directories: {e}")
