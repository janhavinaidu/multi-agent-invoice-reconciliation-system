"""
Configuration management for the application (simple + dependency-safe).
"""

import os
from dotenv import load_dotenv
from typing import List

# Load .env if present
load_dotenv()


class Settings:
    # API Configuration
    APP_NAME: str = "Invoice Reconciliation API"
    APP_VERSION: str = "1.0.0"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = True

    # LLM Configuration
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    LLM_PROVIDER: str = "groq"
    LLM_MODEL: str = "llama-3.3-70b-versatile"
    LLM_TEMPERATURE: float = 0.1
    LLM_MAX_TOKENS: int = 4096

    # CORS Configuration
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
    ]

    # Storage Configuration
    UPLOAD_DIR: str = "uploads"
    OUTPUT_DIR: str = "outputs"
    PO_DATABASE_PATH: str = "../invoice-reconciliation-system/data/purchase_orders.json"
    CONFIG_PATH: str = "../invoice-reconciliation-system/config.yaml"

    # File Upload Configuration
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".png", ".jpg", ".jpeg", ".tiff"]

    # Processing Configuration
    MAX_CONCURRENT_JOBS: int = 5
    JOB_TIMEOUT_SECONDS: int = 300
    STATUS_POLL_INTERVAL: int = 2

    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"


# Global settings instance
settings = Settings()
