from fastapi import APIRouter, Depends, HTTPException
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import (ForgotPasswordRequest, LoginRequest, PasswordChangeRequest,
                              ResetPasswordRequest, TokenResponse, UserCreate, UserPublic)
from app.services import user_service
from app.services.email_service import send_password_reset_email
from app.services.security import (create_access_token, create_reset_token, decode_token,
                                   hash_password, verify_password)

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserPublic, status_code=201)
def register(data: UserCreate, db: Session = Depends(get_db)):
    try:
        return user_service.create_user(db, data)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))

@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = user_service.get_user_by_email(db, str(data.email).lower())
    if not user or not user.password_hash or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")
    token = create_access_token(user.id, user.role)
    return TokenResponse(access_token=token, expires_in=settings.access_token_expire_minutes * 60)

@router.post("/google", response_model=TokenResponse)
def google_login(payload: dict, db: Session = Depends(get_db)):
    # Client obtains an ID token through Google Identity Services and posts it here.
    token = payload.get("id_token")
    if not token or not settings.google_client_id:
        raise HTTPException(status_code=400, detail="id_token and GOOGLE_CLIENT_ID are required")
    try:
        info = id_token.verify_oauth2_token(token, google_requests.Request(), settings.google_client_id)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid Google ID token")
    email = info.get("email", "").lower()
    if not email or not info.get("email_verified"):
        raise HTTPException(status_code=401, detail="Google email is not verified")
    google_sub = info["sub"]
    user = db.query(User).filter(User.google_sub == google_sub).first()
    if not user:
        user = user_service.get_user_by_email(db, email)
        if user:
            # Link accounts only after a verified Google identity has the same email.
            user.google_sub = google_sub
        else:
            user = User(email=email, full_name=info.get("name") or email.split("@")[0],
                        google_sub=google_sub, password_hash=None, role="user")
            db.add(user)
        db.commit()
        db.refresh(user)
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")
    access = create_access_token(user.id, user.role)
    return TokenResponse(access_token=access, expires_in=settings.access_token_expire_minutes * 60)

@router.post("/forgot-password")
def forgot_password(data: ForgotPasswordRequest, db: Session = Depends(get_db)):
    # Same response whether the email exists or not, to reduce account enumeration.
    user = user_service.get_user_by_email(db, str(data.email).lower())
    if user and user.password_hash:
        reset_token = create_reset_token(user.id)
        send_password_reset_email(user.email, reset_token)
    return {"message": "If the account exists, password reset instructions will be sent."}

@router.post("/reset-password")
def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    try:
        payload = decode_token(data.token)
        if payload.get("type") != "password_reset":
            raise HTTPException(status_code=400, detail="Invalid reset token")
        user = db.get(User, int(payload["sub"]))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    user_service.reset_password(db, user, data.new_password)
    return {"message": "Password reset successful. Please log in again."}

@router.post("/change-password")
def change_password(data: PasswordChangeRequest, current_user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    try:
        user_service.change_password(db, current_user, data.current_password, data.new_password)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"message": "Password changed successfully"}

@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    # JWT access tokens are stateless; this endpoint is a client-side logout signal.
    # For immediate server-side revocation, add a token denylist or short-lived tokens + refresh rotation.
    return {"message": "Logged out. Delete the access token on the client."}
