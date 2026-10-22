from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate, UserProfileUpdate, UserAdminUpdate
from app.services.security import hash_password, verify_password

def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)

def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email.lower()))

def create_user(db: Session, data: UserCreate) -> User:
    normalized_email = str(data.email).lower()
    if get_user_by_email(db, normalized_email):
        raise ValueError("An account with this email already exists")
    user = User(email=normalized_email, full_name=data.full_name.strip(),
                password_hash=hash_password(data.password), role="user")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def update_profile(db: Session, user: User, data: UserProfileUpdate) -> User:
    if data.full_name is not None:
        user.full_name = data.full_name.strip()
    db.commit()
    db.refresh(user)
    return user

def update_admin_fields(db: Session, user: User, data: UserAdminUpdate) -> User:
    values = data.model_dump(exclude_unset=True)
    for field, value in values.items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user

def change_password(db: Session, user: User, current_password: str, new_password: str) -> None:
    if not user.password_hash or not verify_password(current_password, user.password_hash):
        raise ValueError("Current password is incorrect or password is managed by Google")
    user.password_hash = hash_password(new_password)
    db.commit()

def reset_password(db: Session, user: User, new_password: str) -> None:
    user.password_hash = hash_password(new_password)
    db.commit()

def delete_user(db: Session, user: User) -> None:
    db.delete(user)
    db.commit()
