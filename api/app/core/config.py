"""
Core configuration for the ticket classifier API.
Uses Pydantic for validation and environment variables with sensible defaults.
"""
from typing import Any, Dict, List, Optional, Union
from pydantic import AnyHttpUrl, PostgresDsn, field_validator
from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv

# Load .env file if it exists
load_dotenv()

class Settings(BaseSettings):
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Automotive Ticket Classifier API"
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []
    
    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # Environment
    ENV: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = ENV != "production"
    LOG_LEVEL: str = "DEBUG" if DEBUG else "INFO"
    
    # Database Configuration
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "auto_classifier")
    SQLALCHEMY_DATABASE_URI: Optional[PostgresDsn] = None
    
    @field_validator("SQLALCHEMY_DATABASE_URI", mode="before")
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        
        # Support SQLite for development/testing
        if os.getenv("USE_SQLITE", "").lower() in ("true", "1", "yes"):
            return f"sqlite:///./auto_classifier.db"
            
        return PostgresDsn.build(
            scheme="postgresql",
            user=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_SERVER"),
            port=values.get("POSTGRES_PORT"),
            path=f"/{values.get('POSTGRES_DB') or ''}",
        )
    
    # Cache Configuration
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD")
    USE_REDIS: bool = os.getenv("USE_REDIS", "").lower() in ("true", "1", "yes")
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "3600"))  # 1 hour default
    
    # Zoho API Configuration
    ZOHO_CLIENT_ID: str = os.getenv("ZOHO_CLIENT_ID", "")
    ZOHO_CLIENT_SECRET: str = os.getenv("ZOHO_CLIENT_SECRET", "")
    ZOHO_REFRESH_TOKEN: str = os.getenv("ZOHO_REFRESH_TOKEN", "")
    ZOHO_BASE_URL: str = os.getenv("ZOHO_BASE_URL", "https://desk.zoho.com/api/v1")
    ZOHO_TIMEOUT: int = int(os.getenv("ZOHO_TIMEOUT", "30"))
    ZOHO_ORG_ID: str = os.getenv("ZOHO_ORG_ID", "")
    ZOHO_REGION: str = "com"  # Default region
    
    # Calculated Zoho URLs
    ZOHO_AUTH_URL: str = "https://accounts.zoho.com/oauth/v2/token"
    
    # OpenAI API Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    OPENAI_TEMPERATURE: float = float(os.getenv("OPENAI_TEMPERATURE", "0.1"))
    OPENAI_MAX_TOKENS: int = int(os.getenv("OPENAI_MAX_TOKENS", "300"))
    
    # Classification Configuration
    VALID_CATEGORIES: List[str] = [
        "Product Activation — New Client",
        "Product Activation — Existing Client", 
        "Product Cancellation",
        "Problem / Bug",
        "General Question",
        "Analysis / Review",
        "Other"
    ]
    
    VALID_SUBCATEGORIES: List[str] = [
        "Import",
        "Export",
        "Sales Data Import", 
        "FB Setup",
        "Google Setup",
        "Other Department",
        "Other",
        "AccuTrade"
    ]
    
    VALID_INVENTORY_TYPES: List[str] = [
        "New",
        "Used",
        "Demo", 
        "New + Used"
    ]
    
    # File paths
    SYNDICATORS_CSV: str = "data/syndicators.csv"
    DEALER_MAPPING_CSV: str = "data/rep_dealer_mapping.csv"
    
    # Performance tuning
    BATCH_SIZE: int = int(os.getenv("BATCH_SIZE", "10"))
    WORKER_CONCURRENCY: int = int(os.getenv("WORKER_CONCURRENCY", "4"))
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-for-dev-only")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    
    class Config:
        case_sensitive = True
        env_file = ".env"

# Create settings instance
settings = Settings()
