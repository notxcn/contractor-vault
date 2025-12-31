"""
Authentication router for email OTP login
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
import jwt

from app.database import get_db
from app.config import get_settings
from app.models.user import User, OTPCode
from app.services.email_service import get_email_service
from app.utils.rate_limiter import limiter

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
@limiter.limit("5/minute")
async def password_login(
    request: Request,
    payload: PasswordLoginRequest,
    db: Session = Depends(get_db)
):
    """Login with email and password."""
    settings = get_settings()
    email = payload.email.lower().strip()
    password = payload.password
    
    # First, try to find user with per-user password
    user = db.query(User).filter(User.email == email).first()
    
    if user and user.password_hash:
        # User has a per-user password set - verify it
        if not user.verify_password(password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
    else:
        # Fall back to admin password for backwards compatibility
        admin_password = getattr(settings, 'admin_password', None)
        if not admin_password:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        if password != admin_password:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Create user if doesn't exist (admin password flow)
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


class RegisterRequest(BaseModel):
    """Register a new user with email and password."""
    email: EmailStr = Field(..., description="Your email address")
    password: str = Field(..., min_length=8, description="Password (min 8 characters)")


class RegisterResponse(BaseModel):
    success: bool
    token: Optional[str] = None
    user: Optional[dict] = None
    message: str


@router.post("/register", response_model=RegisterResponse)
@limiter.limit("3/minute")
async def register(
    request: Request,
    payload: RegisterRequest,
    db: Session = Depends(get_db)
):
    """Register a new user with email and password."""
    email = payload.email.lower().strip()
    password = payload.password
    
    # Check if user already exists with a password
    existing_user = db.query(User).filter(User.email == email).first()
    
    if existing_user and existing_user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists. Please login instead."
        )
    
    # Create or update user with password
    if existing_user:
        # User exists but has no password (created via OTP) - add password
        user = existing_user
    else:
        # Create new user
        user = User(
            id=User.generate_id(),
            email=email,
            created_at=datetime.now(timezone.utc)
        )
        db.add(user)
    
    # Set password
    user.set_password(password)
    user.last_login = datetime.now(timezone.utc)
    db.commit()
    
    # Create token
    token = create_auth_token(user.id, user.email)
    
    logger.info(f"User {email} registered successfully")
    
    return RegisterResponse(
        success=True,
        token=token,
        user={"id": user.id, "email": user.email},
        message="Account created successfully"
    )


@router.post("/logout")
async def logout():
    """Logout - client should clear token."""
    return {"success": True, "message": "Logged out successfully"}


# ===== PASSWORD RESET =====

class RequestResetRequest(BaseModel):
    """Request password reset."""
    email: EmailStr = Field(..., description="Email address for password reset")


class RequestResetResponse(BaseModel):
    success: bool
    message: str


class ResetPasswordRequest(BaseModel):
    """Reset password with token."""
    token: str = Field(..., description="Password reset token from email")
    new_password: str = Field(..., min_length=8, description="New password (min 8 characters)")


class ResetPasswordResponse(BaseModel):
    success: bool
    message: str


def create_reset_token(user_id: str, email: str) -> str:
    """Create a password reset JWT token (valid for 1 hour)."""
    settings = get_settings()
    payload = {
        "sub": user_id,
        "email": email,
        "type": "password_reset",
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=1)
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_reset_token(token: str) -> Optional[dict]:
    """Decode and validate password reset token."""
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        if payload.get("type") != "password_reset":
            return None
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


@router.post("/request-reset", response_model=RequestResetResponse)
@limiter.limit("3/minute")
async def request_reset(
    request: Request,
    payload: RequestResetRequest,
    db: Session = Depends(get_db)
):
    """Request a password reset email."""
    email = payload.email.lower().strip()
    
    # Find user
    user = db.query(User).filter(User.email == email).first()
    
    # Always return success to prevent email enumeration
    if not user:
        logger.warning(f"Password reset requested for non-existent email: {email}")
        return RequestResetResponse(
            success=True,
            message="If an account exists with this email, you will receive a password reset link."
        )
    
    # Create reset token
    reset_token = create_reset_token(user.id, user.email)
    reset_url = f"https://www.shadowkey.org/reset-password?token={reset_token}"
    
    # Try to send email
    try:
        email_service = get_email_service()
        await email_service.send_email(
            to_email=email,
            subject="🔐 Reset Your ShadowKey Password",
            html_content=f"""
            <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto; background: #0f172a; padding: 40px; border-radius: 16px;">
                <h1 style="color: #22d3ee;">ShadowKey Password Reset</h1>
                <p style="color: #e2e8f0;">You requested a password reset for your ShadowKey account.</p>
                <p style="color: #e2e8f0;">Click the button below to set a new password. This link expires in 1 hour.</p>
                <div style="text-align: center; margin: 32px 0;">
                    <a href="{reset_url}" style="background: linear-gradient(to right, #06b6d4, #3b82f6); color: white; padding: 16px 32px; border-radius: 8px; text-decoration: none; font-weight: bold;">Reset Password</a>
                </div>
                <p style="color: #94a3b8; font-size: 14px;">If you didn't request this, you can safely ignore this email.</p>
                <p style="color: #64748b; font-size: 12px; margin-top: 32px;">ShadowKey Security Team</p>
            </div>
            """
        )
        logger.info(f"Password reset email sent to {email}")
    except Exception as e:
        # If email fails, log the token for debugging (remove in production)
        logger.error(f"Failed to send reset email: {e}")
        logger.info(f"Password reset token for {email}: {reset_token}")
    
    return RequestResetResponse(
        success=True,
        message="If an account exists with this email, you will receive a password reset link."
    )


@router.post("/reset-password", response_model=ResetPasswordResponse)
@limiter.limit("5/minute")
async def reset_password(
    request: Request,
    payload: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """Reset password with a valid reset token."""
    # Decode token
    token_data = decode_reset_token(payload.token)
    
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token. Please request a new password reset."
        )
    
    # Find user
    user = db.query(User).filter(User.id == token_data.get("sub")).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found. Please contact support."
        )
    
    # Set new password
    user.set_password(payload.new_password)
    db.commit()
    
    logger.info(f"Password reset successful for {user.email}")
    
    return ResetPasswordResponse(
        success=True,
        message="Password reset successful! You can now log in with your new password."
    )
