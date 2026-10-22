from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.api.deps import get_current_user, require_admin
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserAdminUpdate, UserProfileUpdate, UserPublic
from app.services import user_service

router = APIRouter(tags=["Users"])

@router.get("/users/me", response_model=UserPublic)
def read_my_profile(current_user: User = Depends(get_current_user)):
    return current_user

@router.patch("/users/me", response_model=UserPublic)
def update_my_profile(data: UserProfileUpdate, current_user: User = Depends(get_current_user),
                      db: Session = Depends(get_db)):
    return user_service.update_profile(db, current_user, data)

@router.delete("/users/me", status_code=204)
def delete_my_account(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    user_service.delete_user(db, current_user)
    return None

@router.get("/admin/users", response_model=list[UserPublic])
def list_users(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    return list(db.scalars(select(User).order_by(User.id)).all())

@router.get("/admin/users/{user_id}", response_model=UserPublic)
def read_user(user_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    user = user_service.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.patch("/admin/users/{user_id}", response_model=UserPublic)
def admin_update_user(user_id: int, data: UserAdminUpdate, db: Session = Depends(get_db),
                      admin: User = Depends(require_admin)):
    user = user_service.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == admin.id and data.role == "user":
        raise HTTPException(status_code=400, detail="Admin cannot remove their own admin role")
    return user_service.update_admin_fields(db, user, data)

@router.delete("/admin/users/{user_id}", status_code=204)
def admin_delete_user(user_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    user = user_service.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="Admin cannot delete their own account here")
    user_service.delete_user(db, user)
    return None
