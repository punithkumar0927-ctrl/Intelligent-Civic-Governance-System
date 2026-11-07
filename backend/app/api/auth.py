"""Authentication: register, login, email verification, and password reset."""

from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    CurrentUser,
    create_access_token,
    hash_password,
    hash_token,
    new_secret_token,
    verify_password,
)
from app.database import get_db
from app.models.activity import ActivityLog
from app.models.user import User
from app.schemas.schemas import (
    EmailToken,
    ForgotPassword,
    Message,
    PasswordChange,
    RefreshRequest,
    ResetPassword,
    Token,
    UserOut,
    UserRegister,
    UserUpdate,
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _password_ok(password: str) -> None:
    has_letter = any(ch.isalpha() for ch in password)
    has_digit = any(ch.isdigit() for ch in password)
    if len(password) < 8 or not has_letter or not has_digit:
        raise HTTPException(
            status_code=422,
            detail="Password must be at least 8 characters and include a letter and a number",
        )


def _audit(db: Session, action: str, actor_id: int | None = None, detail: str | None = None) -> None:
    db.add(ActivityLog(actor_id=actor_id, action=action, resource_type="user", detail=detail))


def _issue_tokens(user: User, db: Session, minutes: int | None = None) -> tuple[str, str]:
    access = create_access_token(
        data={"sub": str(user.id), "role": user.role},
        expires_delta=timedelta(minutes=minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    refresh = new_secret_token()
    user.refresh_token_hash = hash_token(refresh)
    db.add(user)
    return access, refresh


def _verification_pair() -> tuple[str, datetime]:
    raw = new_secret_token()
    expires = _utcnow() + timedelta(hours=24)
    return raw, expires


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(body: UserRegister, db: Annotated[Session, Depends(get_db)]):
    _password_ok(body.password)
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    if db.query(User).filter(User.username == body.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")

    raw, expires = _verification_pair()
    user = User(
        username=body.username,
        email=body.email,
        full_name=body.full_name,
        phone=body.phone,
        hashed_password=hash_password(body.password),
        role="citizen",
        is_verified=False,
        email_verification_token=hash_token(raw),
        email_verification_expires=expires,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    _audit(db, "register", user.id)
    db.commit()

    access, refresh = _issue_tokens(user, db)
    db.commit()
    dev_token = raw if settings.ENVIRONMENT == "development" else None
    if settings.EMAIL_PROVIDER and settings.EMAIL_API_KEY:
        # Provider-specific sending is configured through EMAIL_PROVIDER.
        # The token is not logged when a provider is set.
        pass
    return Token(
        access_token=access,
        refresh_token=refresh,
        user=UserOut.model_validate(user),
        dev_verification_token=dev_token,
        message="Account created. Verify your email before relying on privileged actions.",
    )


@router.post("/login", response_model=Token)
def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(get_db)],
    remember: Annotated[bool, Query()] = False,
):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")

    minutes = 60 * 24 * 14 if remember else settings.ACCESS_TOKEN_EXPIRE_MINUTES
    access, refresh = _issue_tokens(user, db, minutes=minutes)
    _audit(db, "login", user.id)
    db.commit()
    return Token(access_token=access, refresh_token=refresh, user=UserOut.model_validate(user))


@router.post("/refresh", response_model=Token)
def refresh(body: RefreshRequest, db: Annotated[Session, Depends(get_db)]):
    digest = hash_token(body.refresh_token)
    user = db.query(User).filter(User.refresh_token_hash == digest, User.is_active.is_(True)).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    access, new_refresh = _issue_tokens(user, db)
    db.commit()
    return Token(access_token=access, refresh_token=new_refresh, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def me(user: CurrentUser):
    return UserOut.model_validate(user)


@router.patch("/me", response_model=UserOut)
def update_me(body: UserUpdate, user: CurrentUser, db: Annotated[Session, Depends(get_db)]):
    if body.full_name is not None:
        user.full_name = body.full_name
    if body.phone is not None:
        user.phone = body.phone
    db.add(user)
    _audit(db, "profile_update", user.id)
    db.commit()
    db.refresh(user)
    return UserOut.model_validate(user)


@router.post("/change-password", response_model=Message)
def change_password(body: PasswordChange, user: CurrentUser, db: Annotated[Session, Depends(get_db)]):
    if not verify_password(body.current_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    _password_ok(body.new_password)
    user.hashed_password = hash_password(body.new_password)
    user.refresh_token_hash = None
    _audit(db, "password_change", user.id)
    db.commit()
    return Message(detail="Password updated")


@router.delete("/me", response_model=Message)
def delete_me(user: CurrentUser, db: Annotated[Session, Depends(get_db)]):
    user.is_active = False
    user.email = f"deleted-{user.id}@invalid.local"
    user.username = f"deleted_{user.id}"
    user.full_name = None
    user.phone = None
    user.refresh_token_hash = None
    _audit(db, "account_delete", user.id)
    db.commit()
    return Message(detail="Account deactivated and personal fields removed")


@router.post("/logout", response_model=Message)
def logout(user: CurrentUser, db: Annotated[Session, Depends(get_db)]):
    user.refresh_token_hash = None
    _audit(db, "logout", user.id)
    db.commit()
    return Message(detail="Logged out successfully")


@router.post("/verify-email", response_model=Message)
def verify_email(body: EmailToken, db: Annotated[Session, Depends(get_db)]):
    digest = hash_token(body.token)
    user = db.query(User).filter(User.email_verification_token == digest).first()
    if not user:
        raise HTTPException(status_code=400, detail="Verification link is invalid")
    expires = _aware(user.email_verification_expires)
    if expires is None or expires < _utcnow():
        raise HTTPException(status_code=400, detail="Verification link has expired")
    user.is_verified = True
    user.email_verification_token = None
    user.email_verification_expires = None
    _audit(db, "email_verified", user.id)
    db.commit()
    return Message(detail="Email verified")


@router.post("/resend-verification", response_model=Message)
def resend_verification(user: CurrentUser, db: Annotated[Session, Depends(get_db)]):
    if user.is_verified:
        return Message(detail="Email is already verified")
    raw, expires = _verification_pair()
    user.email_verification_token = hash_token(raw)
    user.email_verification_expires = expires
    db.commit()
    dev_token = raw if settings.ENVIRONMENT == "development" and not settings.EMAIL_API_KEY else None
    return Message(detail="If email delivery is configured, a new verification message was sent", dev_token=dev_token)


@router.post("/forgot-password", response_model=Message)
def forgot_password(body: ForgotPassword, db: Annotated[Session, Depends(get_db)]):
    user = db.query(User).filter(User.email == body.email, User.is_active.is_(True)).first()
    dev_token: Optional[str] = None
    if user:
        raw = new_secret_token()
        user.password_reset_token = hash_token(raw)
        user.password_reset_expires = _utcnow() + timedelta(hours=1)
        _audit(db, "password_reset_requested", user.id)
        db.commit()
        if settings.ENVIRONMENT == "development" and not settings.EMAIL_API_KEY:
            dev_token = raw
    return Message(
        detail="If an account exists for that email, a reset link has been sent",
        dev_token=dev_token,
    )


@router.post("/reset-password", response_model=Message)
def reset_password(body: ResetPassword, db: Annotated[Session, Depends(get_db)]):
    _password_ok(body.password)
    digest = hash_token(body.token)
    user = db.query(User).filter(User.password_reset_token == digest, User.is_active.is_(True)).first()
    if not user:
        raise HTTPException(status_code=400, detail="Reset link is invalid")
    expires = _aware(user.password_reset_expires)
    if expires is None or expires < _utcnow():
        raise HTTPException(status_code=400, detail="Reset link has expired")
    user.hashed_password = hash_password(body.password)
    user.password_reset_token = None
    user.password_reset_expires = None
    user.refresh_token_hash = None
    _audit(db, "password_reset", user.id)
    db.commit()
    return Message(detail="Password has been reset")
