from fastapi import APIRouter, Depends
from sqlmodel import Session

from database import get_session
from deps import get_current_user
from models import User
from schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    LogoutRequest,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    UpdateProfileRequest,
    UserResponse,
    VerifyEmailRequest,
)
from services.auth_service import (
    change_password,
    forgot_password,
    get_user_profile,
    login_user,
    logout_user,
    refresh_token,
    register_user,
    reset_password,
    update_user_profile,
    verify_email,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=201)
def register(body: RegisterRequest, db: Session = Depends(get_session)):
    user = register_user(body.email, body.password, db)
    return UserResponse(
        id=user.id,
        email=user.email,
        is_email_verified=user.is_email_verified,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_session)):
    return login_user(body.email, body.password, db)


@router.post("/refresh", response_model=TokenResponse)
def refresh(body: RefreshRequest, db: Session = Depends(get_session)):
    return refresh_token(body.refresh_token, db)


@router.post("/logout", response_model=MessageResponse)
def logout(body: LogoutRequest, db: Session = Depends(get_session)):
    logout_user(body.refresh_token, db)
    return MessageResponse(message="Logged out successfully")


@router.post("/verify-email", response_model=MessageResponse)
def verify_email_endpoint(
    body: VerifyEmailRequest, db: Session = Depends(get_session)
):
    verify_email(body.token, db)
    return MessageResponse(message="Email verified successfully")


@router.post("/forgot-password", response_model=MessageResponse)
def forgot_password_endpoint(
    body: ForgotPasswordRequest, db: Session = Depends(get_session)
):
    forgot_password(body.email, db)
    return MessageResponse(
        message="If the email exists, a reset link has been sent"
    )


@router.post("/reset-password", response_model=MessageResponse)
def reset_password_endpoint(
    body: ResetPasswordRequest, db: Session = Depends(get_session)
):
    reset_password(body.token, body.new_password, db)
    return MessageResponse(message="Password reset successfully")


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        is_email_verified=current_user.is_email_verified,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
    )


@router.put("/me", response_model=UserResponse)
def update_profile(
    body: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    user = update_user_profile(
        current_user.id, body.model_dump(exclude_unset=True), db
    )
    return UserResponse(
        id=user.id,
        email=user.email,
        is_email_verified=user.is_email_verified,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.put("/change-password", response_model=MessageResponse)
def change_password_endpoint(
    body: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    change_password(current_user.id, body.old_password, body.new_password, db)
    return MessageResponse(message="Password changed successfully")