"""
User and OTP models for authentication
"""
from datetime import datetime, timezone, timedelta
from sqlalchemy import Column, String, DateTime, Boolean, Integer
from app.database import Base
import secrets


class User(Base):
    """User account for dashboard access."""
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_login = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    
    @classmethod
    def generate_id(cls) -> str:
        return f"user_{secrets.token_hex(12)}"


class OTPCode(Base):
    """One-time password for email verification."""
    __tablename__ = "otp_codes"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, nullable=False, index=True)
    code = Column(String(6), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)
    
    @classmethod
    def generate_code(cls) -> str:
        """Generate a 6-digit OTP code."""
        return str(secrets.randbelow(900000) + 100000)
    
    @classmethod
    def create(cls, email: str, expires_minutes: int = 10) -> "OTPCode":
        """Create a new OTP code for an email."""
        now = datetime.now(timezone.utc)
        return cls(
            email=email.lower().strip(),
            code=cls.generate_code(),
            created_at=now,
            expires_at=now + timedelta(minutes=expires_minutes),
            used=False
        )
    
    def is_valid(self) -> bool:
        """Check if OTP is still valid."""
        now = datetime.now(timezone.utc)
        expires = self.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        return not self.used and expires > now
