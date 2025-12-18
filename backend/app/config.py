"""
Contractor Vault - Configuration Module
SOC2 Compliant: Fail-fast on missing required environment variables
"""
from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
import logging

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    SOC2 Requirement: All sensitive configurations must be externalized.
    """
    
    # Required security keys - application will fail to start if missing
    fernet_key: str = Field(..., description="Fernet symmetric encryption key")
    jwt_secret: str = Field(..., description="JWT signing secret")
    
    # Database
    database_url: str = Field(
        default="sqlite:///./contractor_vault.db",
        description="SQLAlchemy database URL"
    )
    
    # Application settings
    app_name: str = Field(default="ContractorVault")
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")
    
    # Token settings
    default_token_duration_minutes: int = Field(
        default=60,
        description="Default session token validity in minutes"
    )
    max_token_duration_minutes: int = Field(
        default=480,
        description="Maximum allowed token duration (8 hours)"
    )
    
    # JWT settings
    jwt_algorithm: str = Field(default="HS256")
    jwt_issuer: str = Field(default="contractor-vault")
    
    # Discord webhook (optional)
    discord_webhook_url: Optional[str] = Field(
        default=None,
        description="Discord webhook URL for notifications (optional)"
    )
    
    # Resend API for email (optional)
    resend_api_key: Optional[str] = Field(
        default=None,
        description="Resend API key for sending OTP emails"
    )
    
    @field_validator("fernet_key")
    @classmethod
    def validate_fernet_key(cls, v: str) -> str:
        """Validate Fernet key format."""
        if not v or v == "your-fernet-key-here":
            raise ValueError(
                "FERNET_KEY must be set. Generate using: "
                "python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
            )
        # Basic length check for Fernet keys (base64 encoded 32 bytes)
        if len(v) != 44:
            raise ValueError("Invalid Fernet key format. Must be 44 characters.")
        return v
    
    @field_validator("jwt_secret")
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        """Validate JWT secret meets minimum security requirements."""
        if not v or v == "your-jwt-secret-here":
            raise ValueError(
                "JWT_SECRET must be set. Generate using: openssl rand -hex 32"
            )
        if len(v) < 32:
            raise ValueError("JWT_SECRET must be at least 32 characters for security.")
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached application settings.
    SOC2 Requirement: Configuration is immutable after startup.
    """
    logger.info("Loading application configuration...")
    settings = Settings()
    logger.info(f"Configuration loaded for {settings.app_name}")
    return settings
