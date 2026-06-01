from datetime import datetime, timedelta, timezone

import resend
from fastapi import HTTPException, status
from sqlmodel import Session, select

from config import EMAIL_FROM, RESEND_API_KEY
from models import User, VerificationToken, VerificationTokenType
from utils.auth import (
    create_access_token,
    generate_raw_token,
    hash_token,
    hash_password,
    verify_password,
)


def _create_verification_token(
    user_id: str,
    token_type: VerificationTokenType,
    db: Session,
    expires_in: timedelta | None = None,
) -> str:
    if expires_in is None:
        if token_type == VerificationTokenType.email_verification:
            expires_in = timedelta(hours=24)
        elif token_type == VerificationTokenType.password_reset:
            expires_in = timedelta(hours=1)
        elif token_type == VerificationTokenType.refresh_token:
            expires_in = timedelta(days=7)

    raw_token = generate_raw_token()
    token = VerificationToken(
        user_id=user_id,
        token_hash=hash_token(raw_token),
        type=token_type,
        expires_at=datetime.now(timezone.utc) + expires_in,
    )
    db.add(token)
    return raw_token


def register_user(email: str, password: str, db: Session) -> User:
    existing = db.exec(select(User).where(User.email == email)).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = User(email=email, hash_password=hash_password(password))
    db.add(user)
    db.flush()

    raw_token = _create_verification_token(
        user.id, VerificationTokenType.email_verification, db
    )
    db.commit()
    db.refresh(user)

    send_email(
        to=email,
        subject="Verify your email",
        body=f"Click the link to verify: http://localhost:8000/auth/verify-email?token={raw_token}",
    )

    return user


def login_user(email: str, password: str, db: Session) -> dict:
    user = db.exec(select(User).where(User.email == email)).first()
    if not user or not verify_password(password, user.hash_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    access_token = create_access_token({"sub": user.id})
    refresh_token_str = _create_verification_token(
        user.id, VerificationTokenType.refresh_token, db
    )
    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token_str,
        "token_type": "bearer",
    }


def refresh_token(refresh_token_str: str, db: Session) -> dict:
    stored_token = db.exec(
        select(VerificationToken).where(
            VerificationToken.token_hash == hash_token(refresh_token_str),
            VerificationToken.type == VerificationTokenType.refresh_token,
            VerificationToken.used_at.is_(None),
            VerificationToken.expires_at > datetime.now(timezone.utc),
        )
    ).first()

    if not stored_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    user = db.get(User, stored_token.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    stored_token.used_at = datetime.now(timezone.utc)
    db.add(stored_token)

    new_access_token = create_access_token({"sub": user.id})
    new_refresh_token_str = _create_verification_token(
        user.id, VerificationTokenType.refresh_token, db
    )
    db.commit()

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token_str,
        "token_type": "bearer",
    }


def logout_user(refresh_token_str: str, db: Session) -> None:
    stored_token = db.exec(
        select(VerificationToken).where(
            VerificationToken.token_hash == hash_token(refresh_token_str),
            VerificationToken.type == VerificationTokenType.refresh_token,
            VerificationToken.used_at.is_(None),
        )
    ).first()

    if stored_token:
        stored_token.used_at = datetime.now(timezone.utc)
        db.add(stored_token)
        db.commit()


def get_user_profile(user_id: str, db: Session) -> User:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


def send_email(to: str, subject: str, body: str) -> None:
    if not RESEND_API_KEY:
        print(f"[EMAIL STUB] To: {to}, Subject: {subject}")
        return

    resend.api_key = RESEND_API_KEY
    resend.Emails.send(
        {
            "from": EMAIL_FROM,
            "to": to,
            "subject": subject,
            "html": body,
        }
    )


def verify_email(token_str: str, db: Session) -> None:
    stored_token = db.exec(
        select(VerificationToken).where(
            VerificationToken.token_hash == hash_token(token_str),
            VerificationToken.type == VerificationTokenType.email_verification,
            VerificationToken.used_at.is_(None),
            VerificationToken.expires_at > datetime.now(timezone.utc),
        )
    ).first()

    if not stored_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token",
        )

    user = db.get(User, stored_token.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    user.is_email_verified = True
    stored_token.used_at = datetime.now(timezone.utc)
    db.add(user)
    db.add(stored_token)
    db.commit()


def forgot_password(email: str, db: Session) -> None:
    user = db.exec(select(User).where(User.email == email)).first()
    if not user:
        return

    raw_token = _create_verification_token(
        user.id, VerificationTokenType.password_reset, db
    )
    db.commit()

    send_email(
        to=email,
        subject="Reset your password",
        body=f"Click the link to reset: http://localhost:8000/auth/reset-password?token={raw_token}",
    )


def reset_password(token_str: str, new_password: str, db: Session) -> None:
    stored_token = db.exec(
        select(VerificationToken).where(
            VerificationToken.token_hash == hash_token(token_str),
            VerificationToken.type == VerificationTokenType.password_reset,
            VerificationToken.used_at.is_(None),
            VerificationToken.expires_at > datetime.now(timezone.utc),
        )
    ).first()

    if not stored_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    user = db.get(User, stored_token.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    user.hash_password = hash_password(new_password)
    stored_token.used_at = datetime.now(timezone.utc)
    db.add(user)
    db.add(stored_token)
    db.commit()


def update_user_profile(user_id: str, update_data: dict, db: Session) -> User:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    allowed_fields = {"email"}
    for field, value in update_data.items():
        if field in allowed_fields:
            setattr(user, field, value)

    user.updated_at = datetime.now(timezone.utc)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def change_password(
    user_id: str, old_password: str, new_password: str, db: Session
) -> None:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if not verify_password(old_password, user.hash_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect password",
        )

    user.hash_password = hash_password(new_password)
    user.updated_at = datetime.now(timezone.utc)
    db.add(user)
    db.commit()