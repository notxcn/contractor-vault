"""
Authentication router for email OTP login
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
import jwt

from app.database import get_db
from app.config import get_settings
from app.models.user import User, OTPCode
from app.services.email_service import get_email_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["Authentication"])
security = HTTPBearer(auto_error=False)


# ===== SCHEMAS =====

class RequestOTPRequest(BaseModel):
    email: EmailStr = Field(..., description="Email address to send OTP to")


class RequestOTPResponse(BaseModel):
    success: bool
    message: str


class VerifyOTPRequest(BaseModel):
    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6)


class VerifyOTPResponse(BaseModel):
    success: bool
    token: Optional[str] = None
    user: Optional[dict] = None
    message: str


class CurrentUserResponse(BaseModel):
    id: str
    email: str
    created_at: datetime


class PasswordLoginRequest(BaseModel):
    """Login with email and admin password (for when email service is not configured)."""
    email: EmailStr = Field(..., description="Your email address")
    password: str = Field(..., description="Admin password")


class PasswordLoginResponse(BaseModel):
    success: bool
    token: Optional[str] = None
    user: Optional[dict] = None
    message: str


# ===== HELPERS =====

def create_auth_token(user_id: str, email: str) -> str:
    """Create JWT token for authenticated user."""
    settings = get_settings()
    payload = {
        "sub": user_id,
        "email": email,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(days=7)
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_auth_token(token: str) -> Optional[dict]:
    """Decode and validate JWT token."""
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get current authenticated user from JWT token."""
    if not credentials:
        return None
    
    payload = decode_auth_token(credentials.credentials)
    if not payload:
        return None
    
    user = db.query(User).filter(User.id == payload.get("sub")).first()
    return user


async def require_auth(
    user: Optional[User] = Depends(get_current_user)
) -> User:
    """Require authenticated user."""
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return user


# ===== ENDPOINTS =====

@router.post("/request-otp", response_model=RequestOTPResponse)
async def request_otp(
    payload: RequestOTPRequest,
    db: Session = Depends(get_db)
):
    """Request OTP code to be sent to email."""
    email = payload.email.lower().strip()
    
    # Invalidate any existing OTP codes for this email
    db.query(OTPCode).filter(
        OTPCode.email == email,
        OTPCode.used == False
    ).update({"used": True})
    
    # Create new OTP
    otp = OTPCode.create(email)
    db.add(otp)
    db.commit()
    
    # Send email
    email_service = get_email_service()
    sent = await email_service.send_otp(email, otp.code)
    
    if not sent:
        logger.error(f"Failed to send OTP to {email}")
        # Still return success to not leak info about email sending
    
    logger.info(f"OTP requested for {email}")
    
    return RequestOTPResponse(
        success=True,
        message="If this email is valid, you will receive a verification code shortly."
    )


@router.post("/verify-otp", response_model=VerifyOTPResponse)
async def verify_otp(
    payload: VerifyOTPRequest,
    db: Session = Depends(get_db)
):
    """Verify OTP code and return authentication token."""
    email = payload.email.lower().strip()
    code = payload.code.strip()
    
    # Find valid OTP
    otp = db.query(OTPCode).filter(
        OTPCode.email == email,
        OTPCode.code == code,
        OTPCode.used == False
    ).order_by(OTPCode.created_at.desc()).first()
    
    if not otp or not otp.is_valid():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification code"
        )
    
    # Mark OTP as used
    otp.used = True
    
    # Get or create user
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            id=User.generate_id(),
            email=email,
            created_at=datetime.now(timezone.utc)
        )
        db.add(user)
    
    user.last_login = datetime.now(timezone.utc)
    db.commit()
    
    # Create token
    token = create_auth_token(user.id, user.email)
    
    logger.info(f"User {email} authenticated successfully")
    
    return VerifyOTPResponse(
        success=True,
        token=token,
        user={"id": user.id, "email": user.email},
        message="Authentication successful"
    )


@router.get("/me", response_model=CurrentUserResponse)
async def get_me(user: User = Depends(require_auth)):
    """Get current authenticated user."""
    return CurrentUserResponse(
        id=user.id,
        email=user.email,
        created_at=user.created_at
    )


@router.post("/password-login", response_model=PasswordLoginResponse)
async def password_login(
    payload: PasswordLoginRequest,
    db: Session = Depends(get_db)
):
    """Login with email and admin password (fallback when email service is not configured)."""
    settings = get_settings()
    email = payload.email.lower().strip()
    password = payload.password
    
    # Check if admin password is configured
    admin_password = getattr(settings, 'admin_password', None)
    if not admin_password:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Password login not configured. Please set ADMIN_PASSWORD environment variable."
        )
    
    # Verify password
    if password != admin_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password"
        )
    
    # Get or create user
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            id=User.generate_id(),
            email=email,
            created_at=datetime.now(timezone.utc)
        )
        db.add(user)
    
    user.last_login = datetime.now(timezone.utc)
    db.commit()
    
    # Create token
    token = create_auth_token(user.id, user.email)
    
    logger.info(f"User {email} authenticated via password")
    
    return PasswordLoginResponse(
        success=True,
        token=token,
        user={"id": user.id, "email": user.email},
        message="Authentication successful"
    )


@router.post("/logout")
async def logout():
    """Logout - client should clear token."""
    return {"success": True, "message": "Logged out successfully"}
